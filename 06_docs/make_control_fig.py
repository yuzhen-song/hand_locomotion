"""Minimal black-and-white control block diagram (replaces fig8_control).

Orthogonal routing only, one feedback entry into the sum node, no crossing.
Run:  python 06_docs/make_control_fig.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, FancyBboxPatch, Polygon

plt.rcParams["font.family"] = "DejaVu Sans"

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figs")

LW = 1.7
INK = "#111111"
GREY = "#444444"

W, H = 2.60, 1.00          # box size
Y_MAIN = 5.0
Y_BIAS = 7.20
Y_LOW = 1.80
Y_BUS = 0.72
Y_JOIN = 2.72
R_SUM = 0.32

X = {"clock": 1.50, "ref": 4.60, "sum": 7.20, "pd": 9.90, "plant": 13.00,
     "yaw": 5.40, "lat": 9.60}


def box(ax, cx, cy, lines, fs=10.5):
    ax.add_patch(FancyBboxPatch((cx - W / 2, cy - H / 2), W, H,
                                boxstyle="round,pad=0.02,rounding_size=0.11",
                                facecolor="white", edgecolor=INK, lw=LW,
                                zorder=3))
    for i, t in enumerate(lines):
        dy = 0.20 if len(lines) == 2 else 0.0
        ax.text(cx, cy + dy - i * 0.40, t, ha="center", va="center",
                fontsize=fs, color=INK, zorder=4)
    return (cx - W / 2, cy - H / 2, cx + W / 2, cy + H / 2)


def arrow(ax, pts, head=True, lw=LW):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax.plot(xs, ys, color=INK, lw=lw, solid_capstyle="butt",
            solid_joinstyle="miter", zorder=2)
    if head:
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
        d = np.array([x1 - x0, y1 - y0], float)
        d /= np.linalg.norm(d)
        n = np.array([-d[1], d[0]])
        tip = np.array([x1, y1])
        base = tip - d * 0.20
        ax.add_patch(Polygon([tip, base + n * 0.085, base - n * 0.085],
                             closed=True, facecolor=INK, edgecolor=INK,
                             lw=0, zorder=3))


def label(ax, x, y, t, ha="left", fs=9, color=GREY):
    ax.text(x, y, t, ha=ha, va="center", fontsize=fs, color=color, zorder=5)


fig, ax = plt.subplots(figsize=(13.2, 7.8))

# ---- boxes ---------------------------------------------------------------
box(ax, X["clock"], Y_MAIN, ["gait clock", r"$\phi(t)$"])
box(ax, X["ref"], Y_MAIN, ["open-loop ref", r"$q_{\mathrm{ref}}$"])
box(ax, X["pd"], Y_MAIN, ["PD loop", r"$K_p = 40,\ K_d = 4$"])
box(ax, X["plant"], Y_MAIN, ["hand + contacts", "(plant)"])
box(ax, X["sum"], Y_BIAS, ["feedforward bias", r"$b = -0.10$"])
box(ax, X["yaw"], Y_LOW, ["inner: yaw P", r"$K_{\mathrm{yaw}} = 0.5$"], fs=10)
box(ax, X["lat"], Y_LOW, ["outer: lateral P", r"$K_{\mathrm{lat}} = -2,\ \tau = 4\ \mathrm{s}$"],
    fs=10)

# ---- sum node ------------------------------------------------------------
ax.add_patch(FancyBboxPatch((X["sum"] - R_SUM, Y_MAIN - R_SUM), 2 * R_SUM,
                            2 * R_SUM, boxstyle="round,pad=0.02,rounding_size=0.06",
                            facecolor="white", edgecolor=INK, lw=LW, zorder=3))
ax.text(X["sum"], Y_MAIN, r"$\times$", ha="center", va="center", fontsize=19,
        color=INK, zorder=4)
ax.text(X["sum"] + R_SUM + 0.09, Y_MAIN + 0.27, r"$s_{\mathrm{leg}}$", ha="left",
        va="center", fontsize=10.5, color=INK, zorder=4)

# ---- forward path --------------------------------------------------------
arrow(ax, [(X["clock"] + W / 2, Y_MAIN), (X["ref"] - W / 2, Y_MAIN)])
arrow(ax, [(X["ref"] + W / 2, Y_MAIN), (X["sum"] - R_SUM, Y_MAIN)])
arrow(ax, [(X["sum"] + R_SUM, Y_MAIN), (X["pd"] - W / 2, Y_MAIN)])
arrow(ax, [(X["pd"] + W / 2, Y_MAIN), (X["plant"] - W / 2, Y_MAIN)])

# ---- bias into the sum ---------------------------------------------------
arrow(ax, [(X["sum"], Y_BIAS - H / 2), (X["sum"], Y_MAIN + R_SUM)])

# ---- feedback bus --------------------------------------------------------
arrow(ax, [(X["plant"], Y_MAIN - H / 2), (X["plant"], Y_BUS),
           (X["yaw"], Y_BUS), (X["yaw"], Y_LOW - H / 2)])
arrow(ax, [(X["lat"], Y_BUS), (X["lat"], Y_LOW - H / 2)])
ax.add_patch(Circle((X["lat"], Y_BUS), 0.055, facecolor=INK,
                    edgecolor=INK, zorder=4))

# ---- feedback terms merge into one arrow up ------------------------------
arrow(ax, [(X["yaw"], Y_LOW + H / 2), (X["yaw"], Y_JOIN), (X["sum"], Y_JOIN)],
      head=False)
arrow(ax, [(X["lat"], Y_LOW + H / 2), (X["lat"], Y_JOIN), (X["sum"], Y_JOIN)],
      head=False)
ax.add_patch(Circle((X["sum"], Y_JOIN), 0.075, facecolor=INK,
                    edgecolor=INK, zorder=5))
arrow(ax, [(X["sum"], Y_JOIN), (X["sum"], Y_MAIN - R_SUM)])

# ---- labels --------------------------------------------------------------
label(ax, X["plant"] + 0.14, 2.95, "qpos, qvel")
label(ax, X["yaw"] + 0.16, 0.98, "yaw error")
label(ax, X["lat"] + 0.16, 0.98, "lateral error")
label(ax, X["sum"] + 0.10, Y_BIAS - H / 2 - 0.45, "b", fs=8.5)
label(ax, X["sum"] + 0.12, (Y_JOIN + Y_MAIN - R_SUM) / 2 + 0.05, "c",
      fs=9)

ax.text(X["sum"], -0.42,
        r"$s_{\mathrm{leg}}=(1-b_{\mathrm{eff}}\,\sigma)\,(1+c\,\sigma)$,"
        r"   $b_{\mathrm{eff}}=b+K_{\mathrm{lat}}\,\bar x$,"
        r"   $c=K_{\mathrm{yaw}}\,\psi$,   $\sigma=\pm1$"
        r"      clips: $s\in[0.35,1.75]$, $b_{\mathrm{eff}}\in\pm0.7$, $c\in\pm0.4$",
        ha="center", va="center", fontsize=9.5, color=GREY)

ax.set_xlim(-0.4, 14.7)
ax.set_ylim(-0.90, 8.05)
ax.set_aspect("equal")
ax.axis("off")
fig.savefig(os.path.join(FIG, "fig_ctrl_clean.png"), dpi=200,
            bbox_inches="tight", facecolor="white")
fig.savefig(os.path.join(FIG, "fig_ctrl_clean.svg"),
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print("wrote fig_ctrl_clean.png + .svg")
