"""Simplified DH-style side view of one finger (finger A), for writing locomotion
formulas.

Each joint now carries a full right-handed triad: x_i along the link, y_i in
the page (90° CCW from x_i), z_i out of the page (the joint axis).  A legend
spells out the convention, and the base (palm) frame is drawn as well.

All numbers come from the MuJoCo model at the home pose.
"""

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import FancyArrowPatch, Wedge, Rectangle

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01_env"))

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "06_docs", "figs")
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
if os.path.exists(FONT):
    fm.fontManager.addfont(FONT)
plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# ---- geometry from the model (home pose, finger A), cm ----
O = np.array([0.00, 0.00])
P = np.array([5.19, -2.75])
D = np.array([3.48, -5.93])
C = np.array([2.23, -7.85])
l1 = np.linalg.norm(P - O)
l2 = np.linalg.norm(D - P)
l3 = np.linalg.norm(C - D)
ang = lambda a, b: math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))
a1, a2, a3 = ang(O, P), ang(P, D), ang(D, C)

# triad colours: the usual X=red, Y=green, Z=blue
CX, CY, CZ = "#d63b3b", "#2e9e4f", "#2f6fd0"
LINK = "#8a8f9c"
JOINTC = ["#1f77b4", "#e08214", "#27a567"]
THC = "#c2410c"

fig = plt.figure(figsize=(12.2, 7.4), dpi=120)
gs = fig.add_gridspec(2, 2, width_ratios=[1.45, 1.0], height_ratios=[1.0, 0.62],
                      left=0.05, right=0.985, top=0.925, bottom=0.05,
                      wspace=0.14, hspace=0.26)
gsL = gs[:, 0].subgridspec(2, 1, height_ratios=[1.0, 0.13], hspace=0.02)
ax = fig.add_subplot(gsL[0])
ax_leg = fig.add_subplot(gsL[1])
ax_top = fig.add_subplot(gs[0, 1])
ax_eq = fig.add_subplot(gs[1, 1])

# ================================================================== side view
ax.set_aspect("equal")
ax.set_xlim(-3.2, 9.2)
ax.set_ylim(-10.2, 3.2)
ax.set_xticks([])
ax.set_yticks([])
ax.grid(False)
for s in ("top", "right", "bottom", "left"):
    ax.spines[s].set_visible(False)
ax.set_title("侧视图：屈曲链在屈曲平面 Y-Z 内，每个关节附右手坐标系 $x_i y_i z_i$",
             fontsize=11, pad=6)

# palm
ax.add_patch(Rectangle((-2.9, -10.2), 2.0, 13.4, fc="#eceef3", ec="#b9bec9", lw=1.2))
ax.text(-1.9, 2.2, "palm", ha="center", fontsize=9, color="#6b7280")
ax.text(-1.9, 1.2, "（基座）", ha="center", fontsize=8, color="#9aa1ad")

# links
for A, B in ((O, P), (P, D), (D, C)):
    ax.plot([A[0], B[0]], [A[1], B[1]], "-", color=LINK, lw=6.0,
            solid_capstyle="round", zorder=2)

# joint centres
for pt, name, col in ((O, "MCP-FLX", JOINTC[0]), (P, "PIP", JOINTC[1]),
                      (D, "DIP", JOINTC[2])):
    ax.plot(pt[0], pt[1], "o", ms=13, mfc="white", mec=col, mew=2.6, zorder=6)

# angle arcs between consecutive link directions
def theta_arc(center, r, a_from, a_to, label, dr=0.55, label_xy=None):
    th = np.linspace(math.radians(a_from), math.radians(a_to), 60)
    ax.plot(center[0] + r * np.cos(th), center[1] + r * np.sin(th), "-",
            color=THC, lw=1.6, zorder=4)
    mid = math.radians((a_from + a_to) / 2)
    lx, ly = ((center[0] + (r + dr) * math.cos(mid),
               center[1] + (r + dr) * math.sin(mid))
              if label_xy is None else label_xy)
    ax.text(lx, ly, label, color=THC, fontsize=10, ha="center", va="center",
            zorder=7)
    # arrow head at the far end
    ax.add_patch(FancyArrowPatch((center[0] + r * math.cos(th[-2]),
                                  center[1] + r * math.sin(th[-2])),
                                 (center[0] + r * math.cos(th[-1]),
                                  center[1] + r * math.sin(th[-1])),
                                 arrowstyle="-|>", mutation_scale=9, color=THC,
                                 lw=1.4, zorder=7))

theta_arc(O, 2.05, 0, a1, r"$\theta_1$")
theta_arc(P, 1.95, a1, a2, r"$\theta_2$")
theta_arc(D, 1.55, a2, a3, r"$\theta_3$", label_xy=(4.55, -7.05))

# link lengths
def midlabel(A, B, txt, off):
    m = (A + B) / 2
    ax.text(m[0] + off[0], m[1] + off[1], txt, fontsize=9.5, color="#4b5563",
            ha="center", zorder=8,
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.2))
midlabel(O, P, "$l_1$ = %.2f cm" % l1, (1.15, 0.55))
midlabel(P, D, "$l_2$ = %.2f cm" % l2, (-1.55, 0.25))
midlabel(D, C, "$l_3$ = %.2f cm" % l3, (-1.45, -0.35))

# joint names
ax.text(O[0] - 0.15, O[1] + 0.62, "MCP-FLX", fontsize=8.5, color=JOINTC[0],
        ha="right", fontweight="bold")
ax.text(P[0] + 0.25, P[1] + 0.42, "PIP", fontsize=8.5, color=JOINTC[1],
        fontweight="bold")
ax.text(D[0] + 0.25, D[1] - 0.15, "DIP", fontsize=8.5, color=JOINTC[2],
        fontweight="bold")

# triads
def triad(origin, ang_deg, tag, L=1.75, Lz=None, lw=1.8, alpha=1.0, dashed_y=False):
    """x along the link, y = z x x inside the page, z out of the page."""
    a = math.radians(ang_deg)
    ux = np.array([math.cos(a), math.sin(a)])
    uy = np.array([-math.sin(a), math.cos(a)])
    ax.add_patch(FancyArrowPatch(origin, origin + ux * L, arrowstyle="-|>",
                                 mutation_scale=13, color=CX, lw=lw, alpha=alpha,
                                 zorder=7, shrinkA=0, shrinkB=0))
    ax.add_patch(FancyArrowPatch(origin, origin + uy * L * 0.78, arrowstyle="-|>",
                                 mutation_scale=13, color=CY, lw=lw, alpha=alpha,
                                 ls="--" if dashed_y else "-", zorder=7,
                                 shrinkA=0, shrinkB=0))
    # z: out of the page -> circle with a dot
    r = 0.34
    ax.add_patch(plt.Circle(origin, r, fill=False, ec=CZ, lw=1.6, alpha=alpha, zorder=7))
    ax.plot(origin[0], origin[1], ".", ms=4.2, color=CZ, alpha=alpha, zorder=8)
    # labels
    ax.text(origin[0] + ux[0] * (L + 0.26), origin[1] + ux[1] * (L + 0.26),
            "$x_{%s}$" % tag, color=CX, fontsize=10.5, ha="center", va="center",
            zorder=9)
    ax.text(origin[0] + uy[0] * (L * 0.78 + 0.30),
            origin[1] + uy[1] * (L * 0.78 + 0.30), "$y_{%s}$" % tag, color=CY,
            fontsize=10.5, ha="center", va="center", zorder=9)
    ax.text(origin[0] + 0.46, origin[1] + 0.30, "$z_{%s}$" % tag, color=CZ,
            fontsize=10.5, zorder=9)
    ax.text(origin[0] + 0.46, origin[1] + 0.02, "⊙", color=CZ, fontsize=8, zorder=9)

# base frame at MCP-FLX: x0 horizontal to the right (the DH x_0)
triad(O, 0, "0", L=1.30, lw=1.4, alpha=0.7)

triad(O, a1, "1", L=1.75)
triad(P, a2, "2", L=1.55)
triad(D, a3, "3", L=1.20)

# contact
ax.plot(C[0], C[1], "x", ms=13, mew=3.0, color="#b91c1c", zorder=8)
ax.text(C[0] - 0.25, C[1] - 0.75, "接触点", fontsize=8.5, color="#b91c1c", ha="center")

# ================================================================== legend
ax_leg.axis("off")
ax_leg.set_xlim(0, 1)
ax_leg.set_ylim(0, 1)
ax_leg.add_patch(Rectangle((0.001, 0.06), 0.998, 0.88, fc="#f7f8fb",
                           ec="#d8dce6", lw=1.0, transform=ax_leg.transAxes))
ax_leg.text(0.008, 0.50, "约定", fontsize=9.5, fontweight="bold",
            color="#111827", va="center", transform=ax_leg.transAxes)
xa = 0.100
ax_leg.annotate("", xy=(xa + 0.035, 0.50), xytext=(xa, 0.50), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=CX, lw=1.9))
ax_leg.text(xa + 0.045, 0.50, "$x_i$ 沿连杆 i，指向下一关节", fontsize=8.8,
            va="center", color="#374151", transform=ax_leg.transAxes)
xb = 0.378
ax_leg.annotate("", xy=(xb, 0.68), xytext=(xb, 0.34), xycoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color=CY, lw=1.9, ls="--"))
ax_leg.text(xb + 0.014, 0.50, "$y_i = z_i \\times x_i$ 纸面内逆时针 90°", fontsize=8.8,
            va="center", color="#374151", transform=ax_leg.transAxes)
xc = 0.658
ax_leg.add_patch(plt.Circle((xc, 0.50), 0.022, fill=False, ec=CZ, lw=1.6,
                            transform=ax_leg.transAxes, clip_on=False))
ax_leg.plot(xc, 0.50, ".", ms=4, color=CZ, transform=ax_leg.transAxes)
ax_leg.text(xc + 0.035, 0.50, "$z_i$ 关节轴，⊙ 垂直纸面向外", fontsize=8.8,
            va="center", color="#374151", transform=ax_leg.transAxes)


# =================================================================== top view
ax_top.set_aspect("equal")
ax_top.set_xlim(-9, 9)
ax_top.set_ylim(-9.5, 8)
ax_top.grid(alpha=0.2)
ax_top.set_xlabel("X (cm)", fontsize=8)
ax_top.set_ylabel("Y (cm)", fontsize=8)
ax_top.tick_params(labelsize=7)
ax_top.set_title("俯视图：ABD 偏航 $\\theta_0$ 把整条屈曲链转到不同方位", fontsize=9.5)
ax_top.add_patch(Rectangle((-2, -3), 4, 6, fc="#eceef3", ec="#b9bec9", lw=1.2))
ax_top.text(0, 0, "palm", ha="center", va="center", fontsize=8, color="#6b7280")
for ang_deg, col, lab in ((-38, JOINTC[0], "A"), (-13, "#e08214", "B"),
                          (13, JOINTC[2], "C"), (38, "#9b59b6", "D")):
    a = math.radians(ang_deg)
    x, y = 6.4 * math.cos(a), 6.4 * math.sin(a)
    ax_top.plot([0, x], [0, y], "-", color=col, lw=2.2, alpha=0.9)
    ax_top.plot(x, y, "o", ms=6, mfc="white", mec=col, mew=2)
    ax_top.text(x * 1.12, y * 1.12, lab, fontsize=9, color=col, ha="center",
                fontweight="bold")
# world triad
ax_top.add_patch(FancyArrowPatch((0, 0), (2.6, 0), arrowstyle="-|>",
                                 mutation_scale=12, color=CX, lw=1.8))
ax_top.add_patch(FancyArrowPatch((0, 0), (0, 2.6), arrowstyle="-|>",
                                 mutation_scale=12, color=CY, lw=1.8))
ax_top.add_patch(plt.Circle((0, 0), 0.34, fill=False, ec=CZ, lw=1.5))
ax_top.plot(0, 0, ".", ms=4, color=CZ)
ax_top.text(2.75, -0.35, "X", color=CX, fontsize=9)
ax_top.text(0.22, 2.75, "Y", color=CY, fontsize=9)
ax_top.text(0.45, 0.12, "Z ⊙", color=CZ, fontsize=8.5)
ax_top.text(0, -8.6, "$\\theta_0$ = MCP-ABD，绕 Z 轴转动整个屈曲平面",
            fontsize=8.2, ha="center", color="#6b7280")

# ================================================================== equations
ax_eq.axis("off")
lines = [
    "DH 参数（屈曲平面内的简化链）",
    "",
    "i   a_i(cm)   α_i     d_i    θ_i",
    "1   %.2f     0        0      θ1 = MCP-FLX" % l1,
    "2   %.2f     0        0      θ2 = PIP" % l2,
    "3   %.2f     0        0      θ3 = DIP" % l3,
    "0   4.25     90°      0      θ0 = MCP-ABD (yaw)",
    "",
    "θ_i = 绕 z_i 从 x_(i-1) 转到 x_i 的角度",
    "图中 θ_i 是连杆间几何夹角；关节变量 q_i 差一个零位偏置",
    "",
    "前向运动学（平面内）",
    "  y_tip = l1 cosθ1 + l2 cos(θ1+θ2) + l3 cos(θ1+θ2+θ3)",
    "  z_tip = l1 sinθ1 + l2 sin(θ1+θ2) + l3 sin(θ1+θ2+θ3)",
    "",
    "雅可比  J = ∂p/∂θ  （3×4，含 ABD）",
    "锚定    J_c dq = 0  =>  v_body = -J_c,j dq_j",
]
ax_eq.text(0.0, 1.04, "\n".join(lines), fontsize=8.4, va="top",
           transform=ax_eq.transAxes)

fig.suptitle("四指手 · 单指 DH 坐标图（三轴朝向 + 侧视 / 俯视）", fontsize=12.5, y=0.975)
fig.savefig(os.path.join(FIG, "fig_dh_side.png"))
print("saved fig_dh_side.png  l1=%.2f l2=%.2f l3=%.2f cm" % (l1, l2, l3))
print("link angles: %.1f %.1f %.1f deg" % (a1, a2, a3))
print("relative: theta1=%.1f theta2=%.1f theta3=%.1f deg"
      % (a1, a2 - a1, a3 - a2))
