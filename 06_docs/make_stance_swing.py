"""Side-view pair: the stance term vs the swing term.

Drawn to scale from the real finger link lengths (59.9 / 36.1 / 22.9 mm).
Side elevation: travel +Y right, Z up.  The distal joint angle is solved so the
stance fingertips land exactly on the floor.

Run:  python 06_docs/make_stance_swing.py
"""

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Circle, Ellipse, FancyArrowPatch, Rectangle

plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figs")

L1, L2, L3 = 5.99, 3.61, 2.29
MCP_Z = 10.6
PALM_H = 2.4
TIP_R = 0.34

C_BODY = "#1e3a8a"
C_STANCE = "#1d4ed8"
C_SWING = "#ea580c"


def solve_chain(mcp_y, a1, a2, tip_z):
    """Three-segment chain; angles absolute, measured from straight down."""
    s12 = L1 * np.cos(a1) + L2 * np.cos(a2)
    c = float(np.clip((MCP_Z - tip_z - s12) / L3, -1.0, 1.0))
    a3 = float(np.arccos(c))
    best = min((a3, -a3), key=lambda t: abs(np.sin(t) - np.sin(a3)))
    ys, zs = [mcp_y], [MCP_Z]
    y, z = mcp_y, MCP_Z
    for L, a in zip((L1, L2, L3), (a1, a2, best)):
        y += L * np.sin(a)
        z -= L * np.cos(a)
        ys.append(y)
        zs.append(z)
    return np.array(ys), np.array(zs), best


def draw_finger(ax, ys, zs, color, alpha=1.0, lw=4.0, zorder=4):
    ax.plot(ys, zs, "-", color=color, lw=lw, alpha=alpha, zorder=zorder,
            solid_capstyle="round")
    ax.plot(ys[:-1], zs[:-1], "o", ms=6.5, color=color, alpha=alpha,
            zorder=zorder + 1, mec="white", mew=1.2)


def draw_pad(ax, y, z, color, alpha=1.0):
    ax.add_patch(Ellipse((y, z + TIP_R * 0.55), 1.20, TIP_R * 1.15,
                         facecolor=color, alpha=alpha * 0.7, edgecolor="none",
                         zorder=6))
    for dy in (-0.32, -0.11, 0.11, 0.32):
        ax.add_patch(Circle((y + dy, z + TIP_R * 0.45), TIP_R * 0.42,
                            facecolor=color, alpha=alpha, edgecolor="white",
                            lw=0.8, zorder=7))


def draw_floor(ax, y0, y1):
    th = 0.6
    ax.add_patch(Rectangle((y0, -th), y1 - y0, th, facecolor="#e2e8f0",
                           edgecolor="none", zorder=1))
    ax.plot([y0, y1], [0, 0], color="#0f172a", lw=2.6, zorder=2)
    for y in np.arange(y0, y1, 0.95):
        ax.plot([y, y + 0.6], [0, -th], color="#94a3b8", lw=0.9, zorder=1)


def draw_palm(ax, y0=-6.8, y1=6.8):
    ax.add_patch(Rectangle((y0, MCP_Z), y1 - y0, PALM_H, facecolor="#c7d2fe",
                           edgecolor=C_BODY, lw=2, zorder=5))
    ax.text((y0 + y1) / 2, MCP_Z + PALM_H / 2, "palm", ha="center", va="center",
            fontsize=10.5, color="#312e81", zorder=6)


STANCE_POSE = [(-4.3, -0.30, 0.58), (1.7, -0.16, 0.46)]

# ============================================================ 支撑项 / STANCE
fig, ax = plt.subplots(figsize=(10.8, 5.6))
draw_floor(ax, -12.5, 12.5)

for mcp_y, a1, a2 in STANCE_POSE:
    ys, zs, _ = solve_chain(mcp_y, a1, a2, 0.0)
    draw_finger(ax, ys, zs, C_STANCE)
    draw_pad(ax, ys[-1], zs[-1], C_STANCE)
    ax.plot(ys[-1], 0.0, marker="x", ms=12, mew=3.2, color="#b91c1c", zorder=9)

draw_palm(ax)

ax.add_patch(FancyArrowPatch((3.2, MCP_Z + 2.75), (8.4, MCP_Z + 2.75),
                             arrowstyle="-|>", mutation_scale=26, color=C_BODY,
                             lw=3.6, zorder=8))
ax.text(5.8, MCP_Z + 3.22, r"$v_{\rm body}$  身体被推着走 (+Y)", ha="center",
        fontsize=11.5, color=C_BODY, weight="bold")

ax.annotate("脚尖钉住不动\n$\\dot p_c = 0$", xy=(-4.6, 0.55), xytext=(-9.8, 3.4),
            fontsize=11, color="#b91c1c", weight="bold", ha="center",
            arrowprops=dict(arrowstyle="->", color="#b91c1c", lw=1.6,
                            connectionstyle="arc3,rad=0.2"))

ys, zs, _ = solve_chain(*STANCE_POSE[1], 0.0)
ax.add_patch(FancyArrowPatch((ys[1] + 0.45, zs[1] + 0.55),
                             (ys[1] + 1.15, zs[1] + 1.25),
                             arrowstyle="-|>", mutation_scale=15,
                             color="#7c3aed", lw=2.2,
                             connectionstyle="arc3,rad=-0.5", zorder=9))
ax.text(ys[1] + 1.45, zs[1] + 1.2, r"$\dot q_j$", fontsize=14, color="#7c3aed")

ax.text(0, MCP_Z + 6.35, "支撑项 / STANCE　脚不动 → 身体动",
        ha="center", fontsize=15.5, weight="bold", color=C_BODY)
ax.text(0, MCP_Z + 5.18,
        r"$\Delta x_{\rm stance} = \int v_{\rm body}\,dt \; > \; 0$",
        ha="center", fontsize=13.5, color=C_STANCE)
ax.text(0, -1.80, "唯一的净推进来源", ha="center", fontsize=12,
        color=C_STANCE, weight="bold")

ax.set_xlim(-12.5, 12.5)
ax.set_ylim(-2.7, MCP_Z + PALM_H + 5.3)
ax.set_aspect("equal")
ax.axis("off")
fig.savefig(os.path.join(FIG, "fig_p2b_stance_side.png"), dpi=170,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print("wrote fig_p2b_stance_side.png")

# ============================================================== 摆动项 / SWING
fig, ax = plt.subplots(figsize=(10.8, 5.6))
draw_floor(ax, -12.5, 12.5)

for mcp_y, a1, a2 in STANCE_POSE:
    ys, zs, _ = solve_chain(mcp_y, a1, a2, 0.0)
    draw_finger(ax, ys, zs, C_STANCE, alpha=0.28, lw=3.4)

SW_Y = -2.1
ys0, zs0, _ = solve_chain(SW_Y, -0.55, 0.66, 0.0)
ys1, zs1, _ = solve_chain(SW_Y, 0.62, -1.10, 2.0)
draw_finger(ax, ys0, zs0, C_SWING, alpha=0.28, lw=3.4)
draw_finger(ax, ys1, zs1, C_SWING, alpha=1.0, lw=4.4)
ax.plot(ys0[-1], 0, "o", ms=9, mfc="none", mec=C_SWING, mew=2, alpha=0.55,
        zorder=7)
draw_pad(ax, ys1[-1], zs1[-1], C_SWING)

draw_palm(ax)

th = np.linspace(0, 1, 80)
traj_y = ys0[-1] + (ys1[-1] - ys0[-1]) * th
traj_z = np.linspace(0.0, zs1[-1], 80) + 0.85 * np.sin(np.pi * th) + 0.10
ax.plot(traj_y, traj_z, ":", lw=2.2, color=C_SWING, zorder=3)
ax.add_patch(FancyArrowPatch((traj_y[-7], traj_z[-7]), (traj_y[-1], traj_z[-1]),
                             arrowstyle="-|>", mutation_scale=20, color=C_SWING,
                             lw=2.6, zorder=9))

ax.annotate("", xy=(ys1[-1] + 0.05, zs1[-1]), xytext=(ys1[-1] + 0.05, 0),
            arrowprops=dict(arrowstyle="<->", color=C_SWING, lw=1.8))
ax.text(ys1[-1] + 0.45, zs1[-1] / 2, "抬脚 ≈ 2 cm\n(硬上限)", fontsize=10,
        color=C_SWING, va="center", weight="bold")
ax.text(ys1[-1] - 0.2, zs1[-1] + 1.35, "摆动腿", fontsize=10.5, color=C_SWING,
        weight="bold", ha="center")

ax.text(0, MCP_Z + 6.35, "摆动项 / SWING　脚动 → 身体不动",
        ha="center", fontsize=15.5, weight="bold", color=C_SWING)
ax.text(0, MCP_Z + 5.18,
        r"$\Delta x_{\rm swing} = 0$（对地面没有推力）",
        ha="center", fontsize=13.5, color=C_SWING)
ax.text(0, -1.80, "抬不起来 → 前后扫摆互相抵消 → 整步零位移",
        ha="center", fontsize=12, color=C_SWING, weight="bold")

ax.set_xlim(-12.5, 12.5)
ax.set_ylim(-2.7, MCP_Z + PALM_H + 5.3)
ax.set_aspect("equal")
ax.axis("off")
fig.savefig(os.path.join(FIG, "fig_p2c_swing_side.png"), dpi=170,
            bbox_inches="tight", facecolor="white")
plt.close(fig)
print("wrote fig_p2c_swing_side.png")
