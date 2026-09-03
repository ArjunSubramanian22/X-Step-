#!/usr/bin/env python3
"""
Regenerates the three figures used in the X-Step IECBES manuscript.

    python3 make_figures.py

Outputs fig1_system.pdf, fig2_layout.pdf, fig3_budget.pdf in this directory.
Only matplotlib and numpy are required. Every number plotted is taken from the
results tables in main.tex; nothing here is simulated or invented.
"""
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch

# ----------------------------------------------------------------- style ----
plt.rcParams.update({
    "font.family": "serif",
    "font.serif": ["Nimbus Roman", "Times New Roman", "DejaVu Serif"],
    "mathtext.fontset": "stix",
    "font.size": 7.0,
    "axes.labelsize": 7.0,
    "axes.titlesize": 7.5,
    "xtick.labelsize": 6.5,
    "ytick.labelsize": 6.5,
    "legend.fontsize": 6.5,
    "axes.linewidth": 0.6,
    "xtick.major.width": 0.6,
    "ytick.major.width": 0.6,
    "lines.linewidth": 1.0,
    "pdf.fonttype": 42,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.01,
})

COL = 3.45          # IEEE single-column width in inches
INK = "#1a1a1a"
GREY = "#8c8c8c"
ACC = "#20518c"     # informative sites
ACC2 = "#a83232"    # near-free sites

# ============================================================ FIGURE 1 ======
# (a) four-site plantar layout   (b) acquisition-to-alert pipeline


def foot_outline():
    """Stylised right-foot sole outline, anterior up, medial to the left."""
    pts = np.array([
        (-0.055, 0.010), (0.060, 0.015), (0.135, 0.075), (0.165, 0.180),
        (0.170, 0.300), (0.158, 0.430), (0.170, 0.560), (0.185, 0.680),
        (0.180, 0.790), (0.150, 0.875), (0.085, 0.930), (0.000, 0.950),
        (-0.080, 0.940), (-0.140, 0.895), (-0.170, 0.815), (-0.175, 0.720),
        (-0.155, 0.605), (-0.130, 0.470), (-0.150, 0.330), (-0.170, 0.200),
        (-0.150, 0.090),
    ])
    # periodic cubic smoothing by repeated corner cutting (Chaikin)
    p = pts
    for _ in range(4):
        q = np.empty((2 * len(p), 2))
        q[0::2] = 0.75 * p + 0.25 * np.roll(p, -1, axis=0)
        q[1::2] = 0.25 * p + 0.75 * np.roll(p, -1, axis=0)
        p = q
    return p


def fig1(path="fig1_system.pdf"):
    fig = plt.figure(figsize=(COL, 2.15))
    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.45], wspace=0.10)

    # ---- (a) layout -------------------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    out = foot_outline()
    ax.fill(out[:, 0], out[:, 1], facecolor="#f0f0f0", edgecolor=INK, lw=0.8)

    sites = [("HEEL", 0.000, 0.140, ACC),
             ("MET5", 0.120, 0.700, ACC),
             ("MET2", -0.005, 0.775, ACC2),
             ("MET1", -0.110, 0.740, ACC2)]
    for name, x, y, c in sites:
        ax.add_patch(Circle((x, y), 0.042, facecolor=c, edgecolor="white", lw=0.7,
                            zorder=3))
    ax.annotate("MET1", (-0.110, 0.740), (-0.36, 0.870), fontsize=6.2,
                ha="center", arrowprops=dict(arrowstyle="-", lw=0.5, color=GREY))
    ax.annotate("MET2", (-0.005, 0.775), (0.05, 1.010), fontsize=6.2,
                ha="center", arrowprops=dict(arrowstyle="-", lw=0.5, color=GREY))
    ax.annotate("MET5", (0.120, 0.700), (0.38, 0.860), fontsize=6.2,
                ha="center", arrowprops=dict(arrowstyle="-", lw=0.5, color=GREY))
    ax.annotate("HEEL", (0.000, 0.140), (0.34, 0.120), fontsize=6.2,
                ha="center", arrowprops=dict(arrowstyle="-", lw=0.5, color=GREY))

    ax.text(-0.44, 0.42, "medial", fontsize=5.9, color=GREY, rotation=90,
            va="center", ha="center")
    ax.text(0.46, 0.42, "lateral", fontsize=5.9, color=GREY, rotation=270,
            va="center", ha="center")

    ax.set_xlim(-0.56, 0.58)
    ax.set_ylim(-0.06, 1.10)
    ax.set_aspect("equal")
    ax.axis("off")

    # ---- (b) pipeline -----------------------------------------------------
    ax2 = fig.add_subplot(gs[0, 1])
    stages = [
        (r"4$\times$ FSR402, 12-bit ADC", "#eef2f7"),
        (r"ESP32, $f_s=25$ Hz", "#eef2f7"),
        (r"28-byte BLE frame, seq. no.", "#eef2f7"),
        (r"4-s window, $T=100$", "#f7f2ee"),
        (r"feature map $\phi$, $d=59$", "#f7f2ee"),
        (r"logistic regression, 540 par.", "#f0eef7"),
        (r"deterministic alert (75 kPa)", "#f0eef7"),
    ]
    n = len(stages)
    h, gap = 0.098, 0.045
    top = 0.97
    for i, (label, fc) in enumerate(stages):
        y = top - i * (h + gap) - h
        ax2.add_patch(FancyBboxPatch((0.03, y), 0.94, h,
                                     boxstyle="round,pad=0.006,rounding_size=0.02",
                                     facecolor=fc, edgecolor=INK, lw=0.55))
        ax2.text(0.50, y + h / 2, label, ha="center", va="center", fontsize=6.1)
        if i < n - 1:
            ax2.add_patch(FancyArrowPatch((0.50, y - 0.004), (0.50, y - gap + 0.004),
                                          arrowstyle="-|>", mutation_scale=5,
                                          lw=0.55, color=INK))
    ax2.text(1.005, top - 1.5 * (h + gap), "on-insole", fontsize=5.9, color=GREY,
             rotation=270, va="center", ha="left")
    ax2.text(1.005, top - 4.6 * (h + gap), "host", fontsize=5.9, color=GREY,
             rotation=270, va="center", ha="left")
    ax2.set_xlim(0, 1.06)
    ax2.set_ylim(0, 1.0)
    ax2.axis("off")

    fig.text(0.20, 1.005, "(a) sensor layout", ha="center", va="bottom",
             fontsize=7.5)
    fig.text(0.68, 1.005, "(b) acquisition-to-alert path", ha="center",
             va="bottom", fontsize=7.5)

    fig.savefig(path)
    plt.close(fig)


# ============================================================ FIGURE 2 ======
# layout value on the macro-F1 scale and on the Fano information scale

K, HY = 9, math.log2(9)


def fano_bits(acc):
    pe = 1.0 - acc
    hb = 0.0 if pe in (0.0, 1.0) else -pe * math.log2(pe) - (1 - pe) * math.log2(1 - pe)
    return max(0.0, HY - (hb + pe * math.log2(K - 1)))


def fig2(path="fig2_layout.pdf"):
    labels = ["all 4", r"$-$MET1", r"$-$MET2", r"$-$MET5", r"$-$HEEL",
              "MET2+HEEL", "MET1+MET2", "best single", "dummy"]
    f1 = [0.885, 0.883, 0.874, 0.671, 0.657, 0.686, 0.435, 0.420, 0.040]
    acc = [0.885, 0.883, 0.875, 0.686, 0.669, 0.695, 0.459, 0.449, 0.111]
    bits = [fano_bits(a) for a in acc]
    cols = [ACC, ACC2, ACC2, ACC, ACC, ACC, ACC2, GREY, "#cccccc"]

    fig, ax = plt.subplots(figsize=(COL, 1.85))
    x = np.arange(len(labels))
    ax.bar(x, f1, width=0.62, color=cols, edgecolor="none", zorder=2)
    ax.set_ylabel("macro-F1")
    ax.set_ylim(0, 1.0)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=6.0, rotation=30, ha="right",
                       rotation_mode="anchor")
    ax.grid(axis="y", lw=0.35, color="#dddddd", zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)

    ax2 = ax.twinx()
    ax2.plot(x, bits, marker="o", ms=2.6, lw=0.9, color=INK, zorder=4,
             label=r"Fano bound on $I(Y;\hat Y)$")
    ax2.set_ylabel("bits", labelpad=1)
    ax2.set_ylim(0, HY)
    ax2.axhline(HY, ls=":", lw=0.6, color=GREY)
    ax2.text(len(labels) - 0.4, HY - 0.10, r"$H(Y)=\log_2 9$", fontsize=5.8,
             color=GREY, ha="right", va="top")
    for s in ("top",):
        ax2.spines[s].set_visible(False)
    ax2.legend(loc="upper right", frameon=False, bbox_to_anchor=(1.0, 0.90))

    fig.savefig(path)
    plt.close(fig)


# ============================================================ FIGURE 3 ======
# (a) fault sensitivity   (b) fault magnitude against the transducer budget

def fig3(path="fig3_budget.pdf"):
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(COL, 1.70),
                                  gridspec_kw=dict(width_ratios=[1.15, 1.0],
                                                   wspace=0.55))

    # ---- (a) degradation --------------------------------------------------
    names = ["noise\n12 kPa", "loss\n30%", "HEEL\n=0", "bias\n+15 kPa",
             "12.5 Hz"]
    delta = [-0.206, -0.216, -0.629, -0.666, -0.004]
    cols = [ACC, GREY, ACC2, ACC2, GREY]
    y = np.arange(len(names))[::-1]
    ax.barh(y, delta, height=0.6, color=cols, edgecolor="none", zorder=2)
    for yy, d in zip(y, delta):
        ax.text(d - 0.02, yy, f"{d:+.3f}", va="center", ha="right", fontsize=5.8)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=6.0)
    ax.set_xlim(-0.90, 0.06)
    ax.set_xlabel(r"$\Delta$ macro-F1 vs. 0.847 baseline")
    ax.grid(axis="x", lw=0.35, color="#dddddd", zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_title("(a) fault sensitivity", pad=3)

    # ---- (b) error budget -------------------------------------------------
    items = [("noise SD", 12.0, ACC), ("bias", 15.0, ACC2),
             ("cal. MAE", 13.3, INK), ("hysteresis", 15.9, INK),
             ("cal. RMSE", 23.3, INK)]
    yy = np.arange(len(items))[::-1]
    ax2.barh(yy, [v for _, v, _ in items], height=0.6,
             color=[c for _, _, c in items], edgecolor="none", zorder=2)
    ax2.axvspan(13.3, 23.3, color="#000000", alpha=0.07, zorder=1)
    ax2.set_yticks(yy)
    ax2.set_yticklabels([n for n, _, _ in items], fontsize=6.0)
    ax2.set_xlabel("pressure error (kPa)")
    ax2.set_xlim(0, 25)
    ax2.grid(axis="x", lw=0.35, color="#dddddd", zorder=0)
    ax2.set_axisbelow(True)
    for s in ("top", "right", "left"):
        ax2.spines[s].set_visible(False)
    ax2.tick_params(axis="y", length=0)
    ax2.set_title("(b) applied fault vs. budget", pad=3)
    ax2.text(18.3, yy[0] + 0.55, "transducer band", fontsize=5.5,
             color=GREY, ha="center", va="bottom")

    fig.savefig(path)
    plt.close(fig)


if __name__ == "__main__":
    fig1()
    fig2()
    fig3()
    print("wrote fig1_system.pdf, fig2_layout.pdf, fig3_budget.pdf")
