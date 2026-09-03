#!/usr/bin/env python3
"""Compute the seven IECBES manuscript fill-ins from frozen artefacts.

Does not overwrite EHB frozen CSVs. Writes research/results/iecbes_fillins.json.
"""

from __future__ import annotations

import json
import math
import os
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

_ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("MPLCONFIGDIR", str(_ROOT / ".mplconfig"))
(_ROOT / ".mplconfig").mkdir(exist_ok=True)
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from research.experiments.run_research import _cfg, _features, group_cv_oof
from xstep_ml.calibration import SensorCalibration, adc_to_resistance_ohm, load_force_adc_csv
from xstep_ml.data.synthetic_gait import make_cohort_bundle
from xstep_ml.evaluation.baselines import baseline_models
from xstep_ml.evaluation.perturbations import SENSOR_SUBSETS, mask_sites

RES = _ROOT / "research" / "results"
TAB = _ROOT / "research" / "tables"
CAL_CSV = _ROOT / "data" / "calibration" / "four_site_fsr_bench.csv"
B = 2000
SEED = 67
K_CLASSES = 9
HY = math.log2(K_CLASSES)
SITES = ("MET1", "MET2", "MET5", "HEEL")
SITE_INDEX = {name: i for i, name in enumerate(SITES)}


def _round(x: float, n: int = 3) -> float:
    return float(round(float(x), n))


def binary_entropy(pe: float) -> float:
    if pe <= 0.0 or pe >= 1.0:
        return 0.0
    return float(-pe * math.log2(pe) - (1.0 - pe) * math.log2(1.0 - pe))


def fano_pack(accuracy: float) -> dict[str, float]:
    pe = max(0.0, min(1.0, 1.0 - float(accuracy)))
    h_upper = binary_entropy(pe) + pe * math.log2(K_CLASSES - 1)
    info = max(0.0, HY - h_upper)
    return {
        "accuracy": float(accuracy),
        "pe": pe,
        "h_upper": h_upper,
        "I_lower": info,
        "pct_of_HY": 100.0 * info / HY,
    }


def cluster_bootstrap_metric(
    y: np.ndarray,
    pred: np.ndarray,
    groups: np.ndarray,
    n_boot: int = B,
    seed: int = SEED,
    metric: str = "macro_f1",
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    by = {g: np.where(groups == g)[0] for g in uniq}
    n = len(uniq)
    out = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        chosen = rng.choice(uniq, size=n, replace=True)
        idx = np.concatenate([by[g] for g in chosen])
        if metric == "accuracy":
            out[i] = accuracy_score(y[idx], pred[idx])
        else:
            out[i] = f1_score(y[idx], pred[idx], average="macro", zero_division=0)
    return out


def cluster_bootstrap_diff(
    y: np.ndarray,
    pred_a: np.ndarray,
    pred_b: np.ndarray,
    groups: np.ndarray,
    n_boot: int = B,
    seed: int = SEED,
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    uniq = np.unique(groups)
    by = {g: np.where(groups == g)[0] for g in uniq}
    n = len(uniq)
    out = np.empty(n_boot, dtype=np.float64)
    for i in range(n_boot):
        chosen = rng.choice(uniq, size=n, replace=True)
        idx = np.concatenate([by[g] for g in chosen])
        fa = f1_score(y[idx], pred_a[idx], average="macro", zero_division=0)
        fb = f1_score(y[idx], pred_b[idx], average="macro", zero_division=0)
        out[i] = fa - fb
    return out


def percentile_ci(arr: np.ndarray, lo: float = 2.5, hi: float = 97.5) -> tuple[float, float, float]:
    return float(arr.mean()), float(np.percentile(arr, lo)), float(np.percentile(arr, hi))


def holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    adj: dict[str, float] = {}
    running = 0.0
    for i, (name, p) in enumerate(items):
        val = min(1.0, (m - i) * p)
        running = max(running, val)
        adj[name] = running
    return adj


def shapley_from_v(v: dict[frozenset[str], float], players: tuple[str, ...] = SITES) -> dict[str, float]:
    n = len(players)
    phi = {p: 0.0 for p in players}
    for i, player in enumerate(players):
        others = [p for p in players if p != player]
        for r in range(n):
            for subset in combinations(others, r):
                s = frozenset(subset)
                weight = math.factorial(r) * math.factorial(n - r - 1) / math.factorial(n)
                phi[player] += weight * (v[s | {player}] - v[s])
    return phi


def reconstruct_dummy_oof(y: np.ndarray, splits: dict) -> np.ndarray:
    dummy = np.empty(len(y), dtype=object)
    for fold in splits["folds"]:
        tr = np.asarray(fold["train_idx"], dtype=int)
        te = np.asarray(fold["test_idx"], dtype=int)
        values, counts = np.unique(y[tr], return_counts=True)
        dummy[te] = values[int(np.argmax(counts))]
    return dummy.astype(str)


def fit_loglog_xy(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    mask = (x > 0) & (y > 0) & np.isfinite(x) & np.isfinite(y)
    if int(mask.sum()) < 2:
        raise ValueError("need two positive pairs")
    b, a = np.polyfit(np.log10(x[mask]), np.log10(y[mask]), 1)
    return float(a), float(b)  # log10 y = a + b log10 x  →  y = (10^a) x^b


def calibration_coefficients() -> dict:
    rows = load_force_adc_csv(CAL_CSV)
    by_site: dict[str, list[dict]] = defaultdict(list)
    for row in rows:
        by_site[str(row["site"]).lower()].append(row)
    cal = SensorCalibration(site="template")
    out: dict[str, dict] = {}
    for site, site_rows in sorted(by_site.items()):
        adc = np.array([float(r["adc"]) for r in site_rows], dtype=np.float64)
        force = np.array([float(r["force_n"]) for r in site_rows], dtype=np.float64)
        unloaded = adc[force <= 0]
        a0 = float(np.mean(unloaded)) if len(unloaded) else 0.0
        load_mask = force > 0
        r = adc_to_resistance_ohm(adc, cal)
        a_r, b_r = fit_loglog_xy(r[load_mask], force[load_mask])
        k_r = 10.0 ** a_r
        pred_r = np.clip(k_r * np.power(np.clip(r, 1.0, None), b_r), 0.0, 500.0)
        mae_r = float(np.mean(np.abs(pred_r - force)))
        adc_shift = np.clip(adc[load_mask] - a0, 1e-6, None)
        a_a, b_a = fit_loglog_xy(adc_shift, force[load_mask])
        k_a = 10.0 ** a_a
        pred_a = np.zeros_like(force)
        pred_a[load_mask] = np.clip(k_a * np.power(adc_shift, b_a), 0.0, 500.0)
        mae_a = float(np.mean(np.abs(pred_a[load_mask] - force[load_mask])))
        out[site] = {
            "a0_adc": a0,
            "resistance_k": k_r,
            "resistance_b": b_r,
            "resistance_mae_n": mae_r,
            "adc_k": k_a,
            "adc_b": b_a,
            "adc_mae_n": mae_a,
        }
    return out


def layout_value_map() -> dict[frozenset[str], float]:
    df = pd.read_csv(TAB / "sensor_ablation_publication.csv")
    key_to_sites = {
        "4_all": frozenset(SITES),
        "3_no_met1": frozenset(("MET2", "MET5", "HEEL")),
        "3_no_met2": frozenset(("MET1", "MET5", "HEEL")),
        "3_no_met5": frozenset(("MET1", "MET2", "HEEL")),
        "3_no_heel": frozenset(("MET1", "MET2", "MET5")),
        "2_met2_heel": frozenset(("MET2", "HEEL")),
        "2_met1_heel": frozenset(("MET1", "HEEL")),
        "2_met1_met2": frozenset(("MET1", "MET2")),
        "2_met1_met5": frozenset(("MET1", "MET5")),
        "2_met2_met5": frozenset(("MET2", "MET5")),
        "2_met5_heel": frozenset(("MET5", "HEEL")),
        "1_met2": frozenset(("MET2",)),
        "1_heel": frozenset(("HEEL",)),
        "1_met1": frozenset(("MET1",)),
        "1_met5": frozenset(("MET5",)),
    }
    v = {frozenset(): 0.03998060677404628}  # majority dummy macro-F1
    for _, row in df.iterrows():
        v[key_to_sites[str(row["subset"])]] = float(row["Performance"])
    if len(v) != 16:
        missing = [s for s in _all_subsets() if s not in v]
        raise RuntimeError(f"incomplete lattice, missing {missing}")
    return v


def _all_subsets() -> list[frozenset[str]]:
    out = []
    for r in range(5):
        out.extend(frozenset(s) for s in combinations(SITES, r))
    return out


def interactions(v: dict[frozenset[str], float]) -> dict:
    grand = frozenset(SITES)
    empty = frozenset()
    v_s = v[grand]
    v_empty = v[empty]
    delta = {p: v_s - v[grand - {p}] for p in SITES}
    pair_comp = {
        ("MET1", "MET2"): frozenset(("MET5", "HEEL")),
        ("MET5", "HEEL"): frozenset(("MET1", "MET2")),
    }
    out = {
        "v_S": v_s,
        "v_empty": v_empty,
        "total_value": v_s - v_empty,
        "marginals": delta,
        "sum_marginals": float(sum(delta.values())),
    }
    for (i, j), complement in pair_comp.items():
        d_ij = v_s - v[complement]
        d_sum = delta[i] + delta[j]
        out[f"I_{i}_{j}"] = {
            "complement": sorted(complement),
            "v_complement": v[complement],
            "delta_ij": d_ij,
            "delta_i_plus_j": d_sum,
            "I": d_ij - d_sum,
        }
    pairs = {
        frozenset(("MET1", "MET2")): v[frozenset(("MET1", "MET2"))],
        frozenset(("MET1", "MET5")): v[frozenset(("MET1", "MET5"))],
        frozenset(("MET1", "HEEL")): v[frozenset(("MET1", "HEEL"))],
        frozenset(("MET2", "MET5")): v[frozenset(("MET2", "MET5"))],
        frozenset(("MET2", "HEEL")): v[frozenset(("MET2", "HEEL"))],
        frozenset(("MET5", "HEEL")): v[frozenset(("MET5", "HEEL"))],
    }
    best_pair = max(pairs.items(), key=lambda kv: kv[1])
    out["best_two_site"] = {"sites": sorted(best_pair[0]), "macro_f1": best_pair[1]}
    singles = {p: v[frozenset((p,))] for p in SITES}
    best_single = max(singles.items(), key=lambda kv: kv[1])
    out["best_single"] = {"site": best_single[0], "macro_f1": best_single[1]}
    return out


def run_ablation_with_accuracy() -> list[dict]:
    cfg = _cfg()
    bundle = make_cohort_bundle(
        n_subjects=cfg["n_subjects"],
        windows_per_class=cfg["windows_per_class"],
        seed=cfg["seed"],
        hz=cfg["hz"],
        seconds=cfg["seconds"],
        noise_std=cfg["noise_std"],
        label_noise=cfg["label_noise"],
    )
    proto = baseline_models(cfg["seed"])["logreg"]
    rows = []
    for key, keep in SENSOR_SUBSETS.items():
        masked = mask_sites(bundle.windows, keep)
        X = _features(masked, bundle.sample_hz)
        oof, _, folds, _ = group_cv_oof(
            "logreg", proto, X, bundle.y_gait, bundle.subject_id, bundle.feature_names, cfg["n_splits"], cfg["seed"]
        )
        rows.append(
            {
                "subset": key,
                "n_sites": len(keep),
                "macro_f1": float(f1_score(bundle.y_gait, oof, average="macro", zero_division=0)),
                "accuracy": float(accuracy_score(bundle.y_gait, oof)),
                "fold_macro_f1_mean": float(np.mean([r["macro_f1"] for r in folds])),
                "fold_accuracy_mean": float(np.mean([r["accuracy"] for r in folds])),
            }
        )
    return rows, bundle


def fit_models(bundle, names: list[str]) -> dict[str, np.ndarray]:
    cfg = _cfg()
    models = baseline_models(cfg["seed"])
    store = {}
    for name in names:
        oof, _, _, _ = group_cv_oof(
            name,
            models[name],
            bundle.X,
            bundle.y_gait,
            bundle.subject_id,
            bundle.feature_names,
            cfg["n_splits"],
            cfg["seed"],
        )
        store[name] = oof
        print(f"  fitted {name}: macro-F1={f1_score(bundle.y_gait, oof, average='macro', zero_division=0):.4f}", flush=True)
    return store


def main() -> None:
    print("== calibration ==", flush=True)
    cal = calibration_coefficients()
    for site, row in cal.items():
        print(
            f"  {site}: R-model k={row['resistance_k']:.4g} b={row['resistance_b']:.3f} MAE={row['resistance_mae_n']:.3f} N"
            f" | ADC-model k={row['adc_k']:.4g} b={row['adc_b']:.3f} MAE={row['adc_mae_n']:.3f} N a0={row['a0_adc']:.2f}"
        )

    print("== shapley / interactions ==", flush=True)
    v = layout_value_map()
    phi = shapley_from_v(v)
    inter = interactions(v)
    print("  Shapley", {k: round(val, 4) for k, val in phi.items()}, "sum", round(sum(phi.values()), 4))
    print("  best two-site", inter["best_two_site"])
    print("  I_MET1_MET2", inter["I_MET1_MET2"])
    print("  I_MET5_HEEL", inter["I_MET5_HEEL"])

    print("== stored logreg OOF cluster bootstrap ==", flush=True)
    oof_df = pd.read_csv(RES / "oof_logreg_predictions.csv")
    y = oof_df["y_true"].astype(str).to_numpy()
    pred_lr = oof_df["y_pred"].astype(str).to_numpy()
    groups = oof_df["subject_id"].to_numpy()
    splits = json.loads((RES / "splits" / "subject_groupkfold.json").read_text())
    pred_dummy = reconstruct_dummy_oof(y, splits)

    f1_lr = float(f1_score(y, pred_lr, average="macro", zero_division=0))
    acc_lr = float(accuracy_score(y, pred_lr))
    f1_dum = float(f1_score(y, pred_dummy, average="macro", zero_division=0))
    acc_dum = float(accuracy_score(y, pred_dummy))
    print(f"  stored logreg F1={f1_lr:.6f} acc={acc_lr:.6f}")
    print(f"  reconstructed dummy F1={f1_dum:.6f} acc={acc_dum:.6f}")

    boot_lr = cluster_bootstrap_metric(y, pred_lr, groups)
    mean_lr, lo_lr, hi_lr = percentile_ci(boot_lr)
    print(f"  cluster CI logreg F1 {mean_lr:.4f} [{lo_lr:.3f}--{hi_lr:.3f}]")

    diff_dummy = cluster_bootstrap_diff(y, pred_lr, pred_dummy, groups)
    p_raw_dummy = (1.0 + float(np.sum(diff_dummy <= 0.0))) / (B + 1)
    p_holm_dummy = min(1.0, 8.0 * p_raw_dummy)
    print(f"  logreg-dummy bootstrap p_raw={p_raw_dummy:.6g} Holm(m=8)={p_holm_dummy:.6g}")
    subj = np.unique(groups)
    subj_lr = np.array(
        [f1_score(y[groups == g], pred_lr[groups == g], average="macro", zero_division=0) for g in subj]
    )
    subj_dum = np.array(
        [f1_score(y[groups == g], pred_dummy[groups == g], average="macro", zero_division=0) for g in subj]
    )
    n_pos = int(np.sum(subj_lr > subj_dum))
    sign_p = 2.0 ** (-len(subj)) if n_pos == len(subj) else float("nan")
    print(f"  subjects with logreg>dummy: {n_pos}/{len(subj)}; sign-test p={sign_p:.3g}")

    print("== retrain hist_gbm + remaining models for Holm/TOST ==", flush=True)
    cfg = _cfg()
    bundle = make_cohort_bundle(
        n_subjects=cfg["n_subjects"],
        windows_per_class=cfg["windows_per_class"],
        seed=cfg["seed"],
        hz=cfg["hz"],
        seconds=cfg["seconds"],
        noise_std=cfg["noise_std"],
        label_noise=cfg["label_noise"],
    )
    # Align on stored OOF labels as a sanity check that the cohort matches.
    f1_bundle_check = float(f1_score(bundle.y_gait, pred_lr, average="macro", zero_division=0))
    print(f"  stored-OOF vs regenerated labels F1={f1_bundle_check:.6f} (should match {f1_lr:.6f})")
    if not np.array_equal(bundle.y_gait.astype(str), y):
        n_mismatch = int(np.sum(bundle.y_gait.astype(str) != y))
        print(f"  WARNING: {n_mismatch} label mismatches between stored OOF and regenerated cohort")

    y_b = bundle.y_gait.astype(str)
    groups_b = bundle.subject_id
    model_names = [
        "threshold_heuristic",
        "majority",
        "logreg",
        "decision_tree",
        "linear_svm",
        "random_forest",
        "gbm",
        "mlp",
        "hist_gbm",
    ]
    oof_store = fit_models(bundle, model_names)

    p_raw = {}
    non_dummy = [n for n in model_names if n != "majority"]
    for name in non_dummy:
        diffs = cluster_bootstrap_diff(y_b, oof_store[name], oof_store["majority"], groups_b)
        p_raw[name] = (1.0 + float(np.sum(diffs <= 0.0))) / (B + 1)
    p_holm = holm_adjust(p_raw)
    print("  Holm vs dummy:", {k: round(v, 6) for k, v in p_holm.items()})

    diff_tost = cluster_bootstrap_diff(y_b, oof_store["logreg"], oof_store["hist_gbm"], groups_b)
    tost_mean, tost_lo90, tost_hi90 = percentile_ci(diff_tost, 5.0, 95.0)
    delta = 0.02
    equivalent = bool((tost_lo90 > -delta) and (tost_hi90 < delta))
    # TOST p-values against H0: diff <= -delta and H0: diff >= +delta
    p_lower = (1.0 + float(np.sum(diff_tost <= -delta))) / (B + 1)
    p_upper = (1.0 + float(np.sum(diff_tost >= delta))) / (B + 1)
    tost_p = max(p_lower, p_upper)
    print(
        f"  TOST logreg-HGB 90% CI [{tost_lo90:.4f}, {tost_hi90:.4f}] "
        f"equiv={equivalent} p_TOST={tost_p:.4g} mean_diff={tost_mean:.4f}"
    )

    print("== ablation accuracies ==", flush=True)
    ablation_rows, _ = run_ablation_with_accuracy()
    for row in ablation_rows:
        print(f"  {row['subset']}: F1={row['macro_f1']:.4f} acc={row['accuracy']:.4f}")

    # Fano table layouts in manuscript order
    fano_keys = {
        "All four sites": "4_all",
        "Drop MET1": "3_no_met1",
        "Drop MET2": "3_no_met2",
        "Drop MET5": "3_no_met5",
        "Drop HEEL": "3_no_heel",
        "Best two-site layout": "2_met2_heel",
        "MET1+MET2 only": "2_met1_met2",
        "Best single site": "1_heel",
    }
    abl_by_key = {r["subset"]: r for r in ablation_rows}
    dummy_acc = float(accuracy_score(y_b, oof_store["majority"]))
    fano_table = []
    for label, key in fano_keys.items():
        pack = fano_pack(abl_by_key[key]["accuracy"])
        pack["layout"] = label
        pack["subset"] = key
        pack["macro_f1"] = abl_by_key[key]["macro_f1"]
        fano_table.append(pack)
    dummy_pack = fano_pack(dummy_acc)
    dummy_pack.update({"layout": "Majority dummy", "subset": "dummy", "macro_f1": f1_dum})
    # Theoretical chance check at exactly 1/K
    chance_pack = fano_pack(1.0 / K_CLASSES)
    fano_table.append(dummy_pack)

    # Bit-scale interactions using Fano I from accuracies
    def I_of(subset_key: str) -> float:
        return fano_pack(abl_by_key[subset_key]["accuracy"])["I_lower"]

    i_all = I_of("4_all")
    i_empty = chance_pack["I_lower"]
    bit_delta = {
        "MET1": i_all - I_of("3_no_met1"),
        "MET2": i_all - I_of("3_no_met2"),
        "MET5": i_all - I_of("3_no_met5"),
        "HEEL": i_all - I_of("3_no_heel"),
    }
    bit_I_met1_met2 = (i_all - I_of("2_met5_heel")) - (bit_delta["MET1"] + bit_delta["MET2"])
    bit_I_met5_heel = (i_all - I_of("2_met1_met2")) - (bit_delta["MET5"] + bit_delta["HEEL"])

    payload = {
        "protocol": {
            "cluster_bootstrap_B": B,
            "seed": SEED,
            "holm_family_size": 8,
            "tost_delta_macro_f1": delta,
            "note": "Cluster bootstrap resamples virtual subjects with replacement. Frozen EHB CSVs were not overwritten.",
        },
        "calibration": cal,
        "shapley_macro_f1": phi,
        "interactions_macro_f1": inter,
        "production_oof": {
            "macro_f1": f1_lr,
            "accuracy": acc_lr,
            "dummy_macro_f1": f1_dum,
            "dummy_accuracy": acc_dum,
        },
        "cluster_bootstrap_logreg": {
            "mean": mean_lr,
            "ci95_lo": lo_lr,
            "ci95_hi": hi_lr,
        },
        "holm_vs_dummy": {
            "p_raw": p_raw,
            "p_holm": p_holm,
            "sign_test_all_24_subjects": sign_p,
            "stored_oof_p_raw": p_raw_dummy,
            "stored_oof_holm_m8": p_holm_dummy,
        },
        "tost_logreg_vs_hist_gbm": {
            "mean_diff": tost_mean,
            "ci90_lo": tost_lo90,
            "ci90_hi": tost_hi90,
            "delta": delta,
            "equivalent": equivalent,
            "p_tost": tost_p,
            "p_lower": p_lower,
            "p_upper": p_upper,
        },
        "ablation": ablation_rows,
        "fano_table": fano_table,
        "fano_chance_check": chance_pack,
        "interactions_bits": {
            "I_all": i_all,
            "I_empty_chance": i_empty,
            "marginals": bit_delta,
            "sum_marginals": float(sum(bit_delta.values())),
            "I_MET1_MET2": bit_I_met1_met2,
            "I_MET5_HEEL": bit_I_met5_heel,
            "delta_ij_MET1_MET2": i_all - I_of("2_met5_heel"),
            "delta_ij_MET5_HEEL": i_all - I_of("2_met1_met2"),
        },
    }
    out_path = RES / "iecbes_fillins.json"
    out_path.write_text(json.dumps(payload, indent=2, default=str))
    print(f"wrote {out_path}", flush=True)


if __name__ == "__main__":
    main()
