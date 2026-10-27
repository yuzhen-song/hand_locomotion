"""Simplified DH-style side view of one finger (finger A), for writing locomotion
formulas.

Draws the flexion chain (MCP-FLX -> PIP -> DIP -> contact) in the flexion
plane (Y-Z), with link lengths, joint angles, local coordinate frames and the
DH parameters.  A small top view shows the MCP-ABD yaw that orients the whole
flexion plane.  All numbers come from the MuJoCo model at the home pose.
"""

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import FancyArrowPatch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01_env"))
import mujoco  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "06_docs", "figs")
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
if os.path.exists(FONT):
    fm.fontManager.addfont(FONT)
plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ---- geometry from the model (home pose, finger A) ----
# joint anchors (Y, Z) in cm, relative to MCP-FLX
O = np.array([0.0, 0.0])
P = np.array([5.19, -2.75])
D = np.array([3.48, -5.93])
C = np.array([2.23, -7.85])   # contact centroid
l1 = np.linalg.norm(P - O)
l2 = np.linalg.norm(D - P)
l3 = np.linalg.norm(C - D)
ang = lambda a, b: math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
a1, a2, a3 = ang(O, P), ang(P, D), ang(D, C)
# absolute joint angles (from +Y, CCW) at home pose
th1, th2, th3 = a1, a2, a3
# relative angles
rel12 = a2 - a1
rel23 = a3 - a2

fig = plt.figure(figsize=(11.6, 7.0), dpi=120)
gs = fig.add_gridspec(2, 2, width_ratios=[1.5, 1.0], height_ratios=[1.0, 0.55],
                      left=0.06, right=0.98, top=0.93, bottom=0.06,
                      wspace=0.18, hspace=0.32)
ax = fig.add_subplot(gs[:, 0])      # side view
ax_top = fig.add_subplot(gs[0, 1])  # top view
ax_eq = fig.add_subplot(gs[1, 1])   # equations

# ------------------------------------------------------------------ side view
ax.set_aspect("equal")
ax.set_xlim(-2.5, 8.0)
ax.set_ylim(-9.5, 2.5)
ax.grid(alpha=0.25)
ax.set_xlabel("y  (cm)  → 指尖方向")
ax.set_ylabel("z  (cm)  → 下")
ax.set_title("侧视图：屈曲链（flexion chain）在屈曲平面 Y-Z 内", fontsize=11)

# palm wall
ax.add_patch(plt.Rectangle((-2.2, -10), 2.0, 12, fc="#e8e8e8", ec="0.4", lw=1.2))
ax.text(-1.2, 1.6, "palm", ha="center", fontsize=9, color="0.4")
ax.text(-1.2, 0.6, "(base)", ha="center", fontsize=8, color="0.5")

# links
for A, B, col, lw in ((O, P, "tab:blue", 3.5), (P, D, "tab:orange", 3.5),
                       (D, C, "tab:green", 3.5)):
    ax.plot([A[0], B[0]], [A[1], B[1]], "-", color=col, lw=lw, solid_capstyle="round")
# joints
for pt, name, col in ((O, "MCP-FLX", "tab:blue"), (P, "PIP", "tab:orange"),
                      (D, "DIP", "tab:green"), (C, "contact", "crimson")):
    ax.plot(pt[0], pt[1], "o", ms=11, mfc="white", mec=col, mew=2.2)
    ax.text(pt[0] + 0.25, pt[1] + 0.25, name, fontsize=8.5, color=col,
            fontweight="bold")
# tip contact marker
ax.plot(C[0], C[1], "x", ms=12, mew=2.6, color="crimson")
ax.text(C[0] + 0.3, C[1] - 0.4, "contact point", fontsize=8, color="crimson")

# link length labels
def midlabel(A, B, txt, off=(0, 0.35)):
    m = (A + B) / 2
    ax.text(m[0] + off[0], m[1] + off[1], txt, fontsize=9, color="0.25",
            ha="center", bbox=dict(fc="white", ec="none", alpha=0.7, pad=1))
midlabel(O, P, "l1 = %.2f cm" % l1, off=(0.6, 0.1))
midlabel(P, D, "l2 = %.2f cm" % l2, off=(-0.9, 0.0))
midlabel(D, C, "l3 = %.2f cm" % l3, off=(-0.8, 0.0))

# joint angle arcs
def arc(ax, center, r, a0, a1, color, label, lr=0.15):
    ts = np.linspace(math.radians(a0), math.radians(a1), 40)
    xs = center[0] + r * np.cos(ts)
    ys = center[1] + r * np.sin(ts)
    ax.plot(xs, ys, "-", color=color, lw=1.4)
    m = (a0 + a1) / 2
    ax.text(center[0] + (r + lr) * math.cos(math.radians(m)),
            center[1] + (r + lr) * math.sin(math.radians(m)),
            label, fontsize=9, color=color, ha="center", va="center")

arc(ax, O, 1.6, -60, 0, "tab:blue", "$\\theta_1$")
arc(ax, P, 1.2, a1 - 50, a1, "tab:orange", "$\\theta_2$")
arc(ax, D, 0.9, a2 - 30, a2, "tab:green", "$\\theta_3$")

# local coordinate frames (z into page = ⊗, x along link)
def frame(ax, pt, ang_deg, col, name, length=1.6):
    ang = math.radians(ang_deg)
    x = np.array([math.cos(ang), math.sin(ang)]) * length
    ax.add_patch(FancyArrowPatch(pt, pt + x, arrowstyle="-|>", mutation_scale=11,
                                 color=col, lw=1.5))
    ax.text(pt[0] + x[0] + 0.15, pt[1] + x[1] + 0.15, "x%d" % name, fontsize=8,
            color=col)
    ax.plot([pt[0] - 0.30], [pt[1] + 0.42], "o", ms=7, mfc="white", mec="0.45",
            mew=1.1, zorder=6)
    ax.plot([pt[0] - 0.30], [pt[1] + 0.42], ".", ms=2.2, color="0.45", zorder=7)
    ax.text(pt[0] - 0.12, pt[1] + 0.40, "z%d" % name, fontsize=7.5, color="0.45")

frame(ax, O, a1, "tab:blue", 1, length=1.9)
frame(ax, P, a2, "tab:orange", 2, length=1.6)
frame(ax, D, a3, "tab:green", 3, length=1.3)

# ground line
ax.axhline(-9.0, color="0.4", lw=1.2, ls="--")
ax.text(7.0, -8.7, "ground", fontsize=8, color="0.4")

# ------------------------------------------------------------------ top view
ax_top.set_aspect("equal")
ax_top.set_xlim(-8, 8)
ax_top.set_ylim(-8, 8)
ax_top.grid(alpha=0.25)
ax_top.set_xlabel("x (cm)", fontsize=8)
ax_top.set_ylabel("y (cm)", fontsize=8)
ax_top.set_title("俯视图：MCP-ABD 偏航 θ0 把整条屈曲链转到不同的方位", fontsize=9)
# palm
ax_top.add_patch(plt.Rectangle((-2, -3), 4, 6, fc="#e8e8e8", ec="0.4", lw=1.2))
ax_top.text(0, 0, "palm", ha="center", fontsize=8, color="0.4")
# four fingers spread
for ang_deg, col, lab in ((-36, "tab:blue", "A"), (36, "tab:orange", "B"),
                          (144, "tab:green", "C"), (216, "tab:red", "D")):
    a = math.radians(ang_deg)
    x = 6 * math.cos(a)
    y = 6 * math.sin(a)
    ax_top.plot([0, x], [0, y], "-", color=col, lw=2.0)
    ax_top.plot(x, y, "o", ms=6, color=col)
    ax_top.text(x + 0.3, y + 0.3, lab, fontsize=9, color=col, fontweight="bold")
ax_top.annotate("", xy=(5, 0), xytext=(0, 0),
                arrowprops=dict(arrowstyle="-|>", color="0.3", lw=1.2))
ax_top.text(5.2, 0.2, "θ0", fontsize=9, color="0.3")
ax_top.text(0, -7.2, "θ0 = MCP-ABD：把屈曲平面绕世界 Z 转", fontsize=8,
            ha="center", color="0.4")

# ------------------------------------------------------------------ equations
ax_eq.axis("off")
lines = [
    "DH 参数（简化平面链，屈曲平面内）",
    "",
    "i   a_i(cm)   alpha_i   d_i    theta_i",
    "1   %.2f      0         0      theta1 = MCP-FLX" % l1,
    "2   %.2f      0         0      theta2 = PIP" % l2,
    "3   %.2f      0         0      theta3 = DIP" % l3,
    "0   4.25      90        0      theta0 = MCP-ABD (yaw)",
    "",
    "前向运动学（屈曲平面内，y 横向、z 竖直）",
    "  y_tip = l1 cos t1 + l2 cos(t1+t2) + l3 cos(t1+t2+t3)",
    "  z_tip = l1 sin t1 + l2 sin(t1+t2) + l3 sin(t1+t2+t3)",
    "",
    "雅可比：尖端速度 -> 关节速度",
    "  [dy/dt]   [-l1 s1 -l2 s12 -l3 s123  -l2 s12 -l3 s123  -l3 s123] [dq1/dt]",
    "  [dz/dt] = [ l1 c1 +l2 c12 +l3 c123   l2 c12 +l3 c123   l3 c123] [dq2/dt]",
    "                                                                 [dq3/dt]",
    "",
    "锚定条件（尖端不动）: dy/dt = 0, dz/dt = 0",
    "  =>  v_body = -J(q) dq/dt    这就是 locomotion 的推进公式",
    "",
    "零位（home）: t1=-1.10  t2=1.60  t3=-0.35  t0=+/-0.63",
    "行程: t1 in [-1.57, 0.23]   t2 in [-0.49, 1.89]   t3 in [-0.35, 1.96]",
]
ax_eq.text(0.0, 1.02, "\n".join(lines), fontsize=8.2, va="top",
           transform=ax_eq.transAxes)

fig.suptitle("四指手 · 单指 DH 简化图（侧视 + 俯视）", fontsize=12, y=0.97)
fig.savefig(os.path.join(FIG, "fig_dh_side.png"))
print("saved fig_dh_side.png")
print("l1=%.2f  l2=%.2f  l3=%.2f cm" % (l1, l2, l3))
print("home angles: %.2f, %.2f, %.2f, %.2f" % (-1.10, 1.60, -0.35, 0.63))
print("joint angles (home, deg): %.1f, %.1f, %.1f" % (th1, th2, th3))
