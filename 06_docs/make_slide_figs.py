"""Figure for slide 1.4 ("Why this is hard") — the three numbers that decide everything.

All numbers are measured from the model (settled stance), not illustrative:
  support polygon 13.64 x 15.59 cm, CoM height 11.20 cm, CoM offset -0.78 cm,
  lateral margins 8.35 / 5.29 cm, tipping angle 25.3 deg, lateral stroke 2.77 cm.

Run:  python 06_docs/make_slide_figs.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figs")

# ---- measured geometry (cm) -------------------------------------------------
TIP = {  # fingertip pad centres, settled stance (bbox = measured support polygon)
    "A": (2.24, 7.75),
    "B": (-9.14, 7.72),
    "C": (4.51, -7.71),
    "D": (-6.90, -7.84),
}
XMIN, XMAX = min(t[0] for t in TIP.values()), max(t[0] for t in TIP.values())
COM = (-0.78, 0.16)
H_COM = 11.20
MARGIN_R = XMAX - COM[0]          # 5.29
MARGIN_L = COM[0] - XMIN          # 8.35
STROKE = 2.77
TILT = np.degrees(np.arctan(MARGIN_R / H_COM))   # 25.3
DRIFT = 18.0                       # cm/s, measured from the residual-RL rollout
CYCLE = 1.6

fig = plt.figure(figsize=(13.2, 4.6))
gs = fig.add_gridspec(1, 3, width_ratios=[1.25, 1.0, 1.05], wspace=0.28)

# ============================================================ panel A: 俯视
ax = fig.add_subplot(gs[0, 0])
order = ["B", "A", "C", "D"]
poly = np.array([TIP[k] for k in order])
ax.add_patch(plt.Polygon(poly, closed=True, facecolor="#cfe3ff",
                         edgecolor="#2563eb", lw=2, alpha=.55, zorder=1))
for k, (x, y) in TIP.items():
    ax.add_patch(plt.Circle((x, y), 0.8, color="#1e3a8a", zorder=4))
    ax.annotate(k, (x, y), textcoords="offset points", xytext=(0, 11),
                ha="center", fontsize=10, color="#1e3a8a", fontweight="bold")

ax.plot(*COM, marker="x", ms=14, mew=3.2, color="crimson", zorder=6)
ax.annotate("质心投影\nCoM", COM, textcoords="offset points", xytext=(0, -30),
            ha="center", fontsize=10, color="crimson", fontweight="bold")

ax.add_patch(plt.Circle(COM, STROKE, fill=False, ls="--", lw=1.8,
                        edgecolor="#7c3aed", zorder=5))
ax.annotate("横向纠偏行程 %.2f cm" % STROKE, (COM[0], COM[1] + STROKE),
            textcoords="offset points", xytext=(0, 8), ha="center",
            fontsize=9, color="#7c3aed", fontweight="bold")

y_arrow = -2.6
ax.annotate("", xy=(XMAX, y_arrow), xytext=(COM[0], y_arrow),
            arrowprops=dict(arrowstyle="<->", color="crimson", lw=2))
ax.text((COM[0] + XMAX) / 2, y_arrow - 1.6, "%.2f cm" % MARGIN_R,
        ha="center", fontsize=11, color="crimson", fontweight="bold")
ax.annotate("", xy=(COM[0], y_arrow - 5.4), xytext=(XMIN, y_arrow - 5.4),
            arrowprops=dict(arrowstyle="<->", color="#64748b", lw=1.6))
ax.text((COM[0] + XMIN) / 2, y_arrow - 7.0, "%.2f cm" % MARGIN_L,
        ha="center", fontsize=10, color="#64748b")

ax.text(0, 1.13, "俯视：支撑多边形 13.64 × 15.59 cm", transform=ax.transAxes,
        ha="center", va="bottom", fontsize=12, fontweight="bold")
ax.set_aspect("equal")
ax.set_xlim(XMIN - 3, XMAX + 3.5)
ax.set_ylim(-11.5, 10.8)
ax.set_xticks([])
ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)

# ======================================================== panel B: 侧视翻倒
ax = fig.add_subplot(gs[0, 1])
ax.axhspan(-3.2, 0, color="#e2e8f0", zorder=0)
ax.plot([-2.5, 11], [0, 0], color="#334155", lw=3, solid_capstyle="butt", zorder=3)
ax.add_patch(plt.Polygon([[0, 0], [MARGIN_R, 0], [0, H_COM]], closed=True,
                         facecolor="#fecaca", edgecolor="none", alpha=.75, zorder=1))
ax.plot(0, H_COM, "x", ms=13, mew=3.2, color="crimson", zorder=6)
ax.annotate("CoM 高 %.2f cm" % H_COM, (0, H_COM), textcoords="offset points",
            xytext=(-14, 6), ha="right", fontsize=10, color="crimson", fontweight="bold")
ax.plot([0, 0], [0, H_COM], ls=":", lw=1.4, color="#64748b", zorder=2)
ax.plot([0, MARGIN_R], [H_COM, 0], lw=2.4, color="#dc2626", zorder=4)
ax.plot([MARGIN_R, MARGIN_R], [0, H_COM], ls=":", lw=1.2, color="#94a3b8", zorder=2)
ax.annotate("", xy=(MARGIN_R, -0.75), xytext=(0, -0.75),
            arrowprops=dict(arrowstyle="<->", color="#dc2626", lw=1.8))
ax.text(MARGIN_R / 2, -2.1, "余量 %.2f cm" % MARGIN_R, ha="center",
        fontsize=10, color="#dc2626", fontweight="bold")
ax.text(MARGIN_R + 0.35, H_COM * 0.40, "越过边缘即\n不可恢复", fontsize=10,
        color="#dc2626", fontweight="bold", va="center")
ax.annotate("", xy=(2.05, 1.55), xytext=(0, 0),
            arrowprops=dict(arrowstyle="-", color="#dc2626", lw=1.4))
ax.text(2.35, 1.9, "θ", fontsize=13, color="#dc2626")
ax.text(0.40, 0.97, "$\\tan\\theta = \\dfrac{%.2f}{%.2f} = %.3f$\n$\\theta = %.1f^\\circ$"
        % (MARGIN_R, H_COM, MARGIN_R / H_COM, TILT),
        transform=ax.transAxes, fontsize=11.5, color="#0f172a", va="top", ha="left",
        bbox=dict(boxstyle="round,pad=0.35", fc="#fff", ec="#cbd5e1", lw=.8))
ax.text(0, 1.13, "侧视：质心越过边缘 → 重力矩由平衡变加速", transform=ax.transAxes,
        ha="center", va="bottom", fontsize=12, fontweight="bold")
ax.set_xlim(-3, 11.5)
ax.set_ylim(-3.2, 14.5)
ax.set_xticks([])
ax.set_yticks([])
for s in ax.spines.values():
    s.set_visible(False)

# =================================================== panel C: 三个数对比
ax = fig.add_subplot(gs[0, 2])
labels = ["侧向余量\nmargin", "纠偏行程\nstroke", "失稳后漂移\n(实测 0.5 s)"]
vals = [MARGIN_R, STROKE, DRIFT * 0.5]
colors = ["#2563eb", "#7c3aed", "#dc2626"]
bars = ax.barh(labels, vals, color=colors, alpha=.88, height=.55)
for b, v in zip(bars, vals):
    ax.text(v + 0.6, b.get_y() + b.get_height() / 2, "%.1f cm" % v,
            va="center", fontsize=11, fontweight="bold", color=b.get_facecolor())
ax.axvline(MARGIN_R, ls="--", lw=1.4, color="#64748b")
ax.annotate("纠偏能力只有余量的 %.0f%%\n→ 出界后救不回来" % (STROKE / MARGIN_R * 100),
            (STROKE, 0.62), textcoords="offset points", xytext=(10, 0),
            fontsize=9.5, color="#7c3aed", va="center")
ax.annotate("18 cm/s：0.5 s 就漂出边界", (DRIFT * 0.5, 1.62),
            textcoords="offset points", xytext=(-8, 0), ha="right",
            fontsize=9.5, color="#dc2626")
ax.text(0, 1.13, "三个数一比就知道为什么难", transform=ax.transAxes,
        ha="center", va="bottom", fontsize=12, fontweight="bold")
ax.set_xlim(0, 16)
ax.set_xlabel("cm", fontsize=10)
ax.invert_yaxis()
ax.tick_params(labelsize=10)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

fig.savefig(os.path.join(FIG, "fig_p1_why_hard.png"), dpi=170, bbox_inches="tight")
plt.close(fig)
print("wrote fig_p1_why_hard.png")
