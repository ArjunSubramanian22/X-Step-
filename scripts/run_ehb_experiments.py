#!/usr/bin/env python3
"""Reproduce EHB 2026 tables and 300 dpi figures.

Subject-grouped evaluation on the in-silico 4-FSR cohort (not IID windows).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.inspection import permutation_importance
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GroupKFold, train_test_split

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from xstep_ml.biomechanics import GaitWindow, extract_features
from xstep_ml.data.synthetic_gait import make_cohort, synthesize_window
from xstep_ml.evaluation.baselines import FEATURE_GROUPS, baseline_models
from xstep_ml.evaluation.stats import bootstrap_metric, mcnemar_b
from xstep_ml.models.gait import GAIT_CLASSES, gait_pipeline, save_artifact, zone_pipeline

FIG = _ROOT / "papers" / "ehb2026" / "figures"
TAB = _ROOT / "papers" / "ehb2026" / "tables"
ART = _ROOT / "artifacts"
DPI = 300


def _style() -> None:
    sns.set_theme(style="whitegrid", font_scale=1.05)
    plt.rcParams.update({
        "figure.dpi": DPI,
        "savefig.dpi": DPI,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })


def _feature_names() -> list[str]:
    frames, _, _ = synthesize_window("normal", np.random.default_rng(0))
    return extract_features(GaitWindow(frames)).names


def group_cv_predict(model_factory, x, y, groups, n_splits=5, seed=67):
    gkf = GroupKFold(n_splits=n_splits)
    oof = np.empty(len(y), dtype=object)
    fold_rows = []
    for fold, (tr, te) in enumerate(gkf.split(x, y, groups), 1):
        clf = model_factory()
        clf.fit(x[tr], y[tr])
        pred = clf.predict(x[te])
        oof[te] = pred
        fold_rows.append({
            "fold": fold,
            "accuracy": float(accuracy_score(y[te], pred)),
            "macro_f1": float(f1_score(y[te], pred, average="macro", zero_division=0)),
            "n_test": int(len(te)),
        })
    return oof.astype(str), fold_rows


def run() -> dict:
    FIG.mkdir(parents=True, exist_ok=True)
    TAB.mkdir(parents=True, exist_ok=True)
    ART.mkdir(parents=True, exist_ok=True)
    _style()
    names = _feature_names()

    x, y_gait, y_zone, groups = make_cohort(
        n_subjects=24, windows_per_class=12, seed=67, noise_std=3.5, label_noise=0.03
    )

    # --- baselines, group CV ---
    baseline_table = []
    oof_store = {}
    for name, proto in baseline_models().items():
        def factory(p=proto):
            from sklearn.base import clone
            return clone(p)

        oof, folds = group_cv_predict(factory, x, y_gait, groups)
        oof_store[name] = oof
        acc = bootstrap_metric(y_gait, oof, "accuracy")
        f1 = bootstrap_metric(y_gait, oof, "macro_f1")
        baseline_table.append({
            "model": name,
            "acc_mean": acc["mean"],
            "acc_ci95": [acc["ci95_lo"], acc["ci95_hi"]],
            "macro_f1_mean": f1["mean"],
            "macro_f1_ci95": [f1["ci95_lo"], f1["ci95_hi"]],
            "fold_macro_f1_mean": float(np.mean([r["macro_f1"] for r in folds])),
            "fold_macro_f1_std": float(np.std([r["macro_f1"] for r in folds])),
        })

    # McNemar RF vs logreg
    mcnemar = mcnemar_b(y_gait, oof_store["random_forest"], oof_store["logreg"])

    # --- ablation on RF ---
    ablation = []
    rf_factory = gait_pipeline
    for gname, selector in FEATURE_GROUPS.items():
        idx = selector(names)
        oof, folds = group_cv_predict(rf_factory, x[:, idx], y_gait, groups)
        f1 = bootstrap_metric(y_gait, oof, "macro_f1")
        ablation.append({"feature_set": gname, "n_features": len(idx), "macro_f1": f1["mean"], "ci95": [f1["ci95_lo"], f1["ci95_hi"]]})

    # --- noise robustness: train 3.5, test other noise with same subjects held out ---
    x_tr, x_te, g_tr, g_te, z_tr, z_te, s_tr, s_te = train_test_split(
        x, y_gait, y_zone, groups, test_size=0.25, random_state=67, stratify=y_gait
    )
    # true subject holdout
    hold_subjects = np.unique(groups)[-6:]
    tr_mask = ~np.isin(groups, hold_subjects)
    te_mask = np.isin(groups, hold_subjects)
    rf = gait_pipeline()
    rf.fit(x[tr_mask], y_gait[tr_mask])
    noise_rows = []
    from xstep_ml.data.synthetic_gait import make_cohort as mc

    for noise in (1.5, 3.5, 7.0, 12.0):
        xt, yt, _, gt = mc(n_subjects=24, windows_per_class=8, seed=99, noise_std=noise, label_noise=0.03)
        m = np.isin(gt, hold_subjects)
        pred = rf.predict(xt[m])
        noise_rows.append({
            "noise_std_kpa": noise,
            "macro_f1": float(f1_score(yt[m], pred, average="macro", zero_division=0)),
            "accuracy": float(accuracy_score(yt[m], pred)),
        })

    # --- permutation importance ---
    rf_full = gait_pipeline()
    rf_full.fit(x[tr_mask], y_gait[tr_mask])
    perm = permutation_importance(
        rf_full, x[te_mask], y_gait[te_mask], n_repeats=8, random_state=67, scoring="f1_macro", n_jobs=-1
    )
    order = np.argsort(perm.importances_mean)[::-1][:15]

    # --- zone model ---
    zone = zone_pipeline()
    zone.fit(x[tr_mask], y_zone[tr_mask])
    zone_pred = zone.predict(x[te_mask])
    zone_f1 = bootstrap_metric(y_zone[te_mask], zone_pred, "macro_f1")

    # persist production models on all data (documented as such)
    save_artifact(gait_pipeline().fit(x, y_gait), "gait_pattern_rf.joblib")
    save_artifact(zone_pipeline().fit(x, y_zone), "high_risk_zone_gbm.joblib")

    # figures
    labels = list(GAIT_CLASSES)
    cm = confusion_matrix(y_gait, oof_store["random_forest"], labels=labels)
    fig, ax = plt.subplots(figsize=(7.2, 6.2))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues", xticklabels=[lab.replace("_", "\n") for lab in labels],
                yticklabels=[lab.replace("_", "\n") for lab in labels], ax=ax)
    ax.set_xlabel("Predicted gait pattern")
    ax.set_ylabel("True gait pattern")
    ax.set_title("Subject-grouped OOF confusion (random forest)")
    fig.savefig(FIG / "fig_gait_confusion.png")
    fig.savefig(FIG / "fig_gait_confusion.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.0, 4.2))
    models = [r["model"] for r in baseline_table]
    means = [r["macro_f1_mean"] for r in baseline_table]
    lo = [r["macro_f1_mean"] - r["macro_f1_ci95"][0] for r in baseline_table]
    hi = [r["macro_f1_ci95"][1] - r["macro_f1_mean"] for r in baseline_table]
    ax.bar(models, means, yerr=[lo, hi], capsize=4, color=sns.color_palette("deep", len(models)))
    ax.set_ylabel("Macro-F1 (bootstrap 95% CI)")
    ax.set_ylim(0, 1.05)
    ax.set_title("Gait classification baselines, 5-fold GroupKFold")
    plt.xticks(rotation=20, ha="right")
    fig.savefig(FIG / "fig_baselines.png")
    fig.savefig(FIG / "fig_baselines.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot([r["noise_std_kpa"] for r in noise_rows], [r["macro_f1"] for r in noise_rows], marker="o")
    ax.set_xlabel("Additive Gaussian noise SD (kPa)")
    ax.set_ylabel("Macro-F1 on held-out subjects")
    ax.set_title("Robustness to FSR noise (subject hold-out)")
    fig.savefig(FIG / "fig_noise.png")
    fig.savefig(FIG / "fig_noise.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    ax.barh([names[i] for i in order][::-1], perm.importances_mean[order][::-1],
            xerr=perm.importances_std[order][::-1], capsize=3)
    ax.set_xlabel("Permutation importance (macro-F1 drop)")
    ax.set_title("Top biomechanical features (held-out subjects)")
    fig.savefig(FIG / "fig_importance.png")
    fig.savefig(FIG / "fig_importance.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.bar([r["feature_set"] for r in ablation], [r["macro_f1"] for r in ablation], color=sns.color_palette("muted"))
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Macro-F1")
    ax.set_title("Feature-group ablation (group CV, random forest)")
    plt.xticks(rotation=15, ha="right")
    fig.savefig(FIG / "fig_ablation.png")
    fig.savefig(FIG / "fig_ablation.pdf")
    plt.close(fig)

    _draw_system(FIG / "fig_system.png")

    report = classification_report(y_gait, oof_store["random_forest"], output_dict=True, zero_division=0)
    payload = {
        "n_windows": int(len(y_gait)),
        "n_subjects": int(len(np.unique(groups))),
        "protocol": "5-fold GroupKFold by virtual subject; 3% label noise; mixed overload severity",
        "baselines": baseline_table,
        "mcnemar_rf_vs_logreg": mcnemar,
        "ablation": ablation,
        "noise": noise_rows,
        "zone_holdout_macro_f1": zone_f1,
        "rf_oof_report": report,
        "top_features": [{"name": names[i], "importance": float(perm.importances_mean[i])} for i in order],
    }
    (TAB / "ehb_results.json").write_text(json.dumps(payload, indent=2))
    _write_csv(TAB / "baselines.csv", baseline_table)
    lines = ["| Model | Accuracy | Macro-F1 | Fold macro-F1 mean (SD) |", "| --- | --- | --- | --- |"]
    for r in baseline_table:
        lines.append(
            f"| {r['model']} | {r['acc_mean']:.3f} [{r['acc_ci95'][0]:.3f}, {r['acc_ci95'][1]:.3f}] | "
            f"{r['macro_f1_mean']:.3f} [{r['macro_f1_ci95'][0]:.3f}, {r['macro_f1_ci95'][1]:.3f}] | "
            f"{r['fold_macro_f1_mean']:.3f} ({r['fold_macro_f1_std']:.3f}) |"
        )
    (TAB / "table1_baselines.md").write_text("\n".join(lines) + "\n")
    print(json.dumps({
        "rf_macro_f1": baseline_table[3]["macro_f1_mean"] if baseline_table[3]["model"]=="random_forest" else
        next(r["macro_f1_mean"] for r in baseline_table if r["model"]=="random_forest"),
        "logreg_macro_f1": next(r["macro_f1_mean"] for r in baseline_table if r["model"]=="logreg"),
        "mcnemar_p": mcnemar["p_approx"],
        "zone_f1": zone_f1["mean"],
    }, indent=2))
    return payload


def _write_csv(path: Path, rows: list[dict]) -> None:
    import csv
    keys = ["model", "acc_mean", "macro_f1_mean", "fold_macro_f1_mean", "fold_macro_f1_std"]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})


def _draw_system(path: Path) -> None:
    fig, ax = plt.subplots(figsize=(8.4, 3.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 3)
    ax.axis("off")
    boxes = [
        (0.2, 1.0, "4-FSR insole\nMET1/2/5+heel\nBLE 25 Hz"),
        (2.5, 1.0, "Biomechanics\nPPP, PTI,\nasymmetry, cadence"),
        (4.8, 1.7, "Gait RF"),
        (4.8, 0.3, "Zone GBM"),
        (6.8, 1.0, "Fusion +\nIWGDF clinical\n+ ulcer CNN"),
        (8.6, 1.0, "Alerts &\nclinician\nreport"),
    ]
    for x, y, t in boxes:
        ax.add_patch(plt.Rectangle((x, y), 1.6, 1.2, fill=True, facecolor="#e8f1fb", edgecolor="#1f4e79", lw=1.4))
        ax.text(x + 0.8, y + 0.6, t, ha="center", va="center", fontsize=8)
    for a, b in [(1.8, 2.5), (4.1, 4.8), (6.4, 6.8), (8.4, 8.6)]:
        ax.annotate("", xy=(b, 1.6), xytext=(a, 1.6),
                    arrowprops=dict(arrowstyle="->", color="#1f4e79", lw=1.3))
    ax.set_title("X-Step inference pipeline", loc="left")
    fig.savefig(path, dpi=DPI)
    fig.savefig(path.with_suffix(".pdf"))
    plt.close(fig)


if __name__ == "__main__":
    run()
