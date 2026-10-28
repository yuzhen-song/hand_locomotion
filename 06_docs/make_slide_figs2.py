"""Slide 2 and Slide 3 figures.

fig_p2_anchor.png   — why stance contact is what pushes the body (J_c q = 0)
fig_p3_fall.png     — the measured residual-RL fall: drift, tilt, and the dead time

Numbers come from the actual rollout (04_checkpoints/residual_last.zip),
sampled every 25 steps at 500 Hz.
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

# ============================================================ fig P2: 锚定
fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.5))
fig.subplots_adjust(wspace=0.13)

L1, L2 = 1.05, 0.75          # 两节指骨长度


def leg_pts(x0, y0, a1, a2):
    x1 = x0 + L1 * np.sin(a1)
    y1 = y0 - L1 * np.cos(a1)
    x2 = x1 + L2 * np.sin(a1 + a2)
    y2 = y1 - L2 * np.cos(a1 + a2)
    return (x0, y0), (x1, y1), (x2, y2)


def draw_leg(ax, x0, y0, a1, a2, color, lw=3.2, alpha=1.0, zorder=3):
    p0, p1, p2 = leg_pts(x0, y0, a1, a2)
    ax.plot([p0[0], p1[0], p2[0]], [p0[1], p1[1], p2[1]], "-o",
            color=color, lw=lw, ms=5, alpha=alpha, zorder=zorder,
            solid_capstyle="round")
    return p2


A1, A2 = -0.50, 0.95
GROUND = leg_pts(0, 0, A1, A2)[2][1]      # 支撑脚尖所在的 y
PALM_Y = 0.0

# ---------------------------------------------------------------- panel (a)
ax = axes[0]
ax.axhspan(GROUND - 0.55, GROUND, color="#e8edf4", zorder=0)
ax.plot([-4.6, 4.6], [GROUND, GROUND], color="#334155", lw=3, zorder=2)
ax.add_patch(plt.Rectangle((-1.6, PALM_Y - 0.05), 3.2, 0.62, facecolor="#c7d2fe",
                           edgecolor="#4338ca", lw=1.6, zorder=4))
ax.text(0, PALM_Y + 0.26, "palm", ha="center", va="center", fontsize=10,
        color="#312e81")

for x0 in (-1.05, 1.05):
    p2 = draw_leg(ax, x0, PALM_Y, A1, A2, "#1d4ed8")
    ax.plot(p2[0], p2[1], "o", ms=11, color="#1d4ed8", zorder=6)
ax.text(-2.55, GROUND - 0.42, "脚尖钉住\n(不滑)", fontsize=9.5, color="#1d4ed8",
        ha="center", weight="bold")

ax.annotate("", xy=(1.02, PALM_Y - 0.62), xytext=(1.30, PALM_Y - 0.42),
            arrowprops=dict(arrowstyle="->", color="#7c3aed", lw=2.2,
                            connectionstyle="arc3,rad=-0.5"))
ax.text(1.72, PALM_Y - 0.50, r"$\dot q_j$", fontsize=15, color="#7c3aed")

ax.annotate("", xy=(-2.45, 1.22), xytext=(-0.45, 1.22),
            arrowprops=dict(arrowstyle="-|>", color="#dc2626", lw=3.2,
                            mutation_scale=22))
ax.text(-1.45, 1.52, r"$v_{\rm body}$", fontsize=15, color="#dc2626", ha="center")
ax.text(0, 2.05, "关节一转，身体被反推", fontsize=11.5, color="#dc2626",
        ha="center", weight="bold")

ax.text(0.3, GROUND - 1.28, r"$J_c\,\dot q = 0$", fontsize=17, color="#0f172a",
        ha="center", bbox=dict(boxstyle="round,pad=0.4", fc="#fff", ec="#94a3b8"))
ax.text(0.3, GROUND - 2.16, r"$\Rightarrow\; v_{\rm body} = -J_c^{-1}J_j\,\dot q_j$",
        fontsize=15, color="#0f172a", ha="center")

ax.set_title("① 支撑相：脚不动 → 身体动", fontsize=13, weight="bold", pad=8)
ax.set_xlim(-4.6, 4.6)
ax.set_ylim(GROUND - 2.7, 2.5)
ax.axis("off")

# ---------------------------------------------------------------- panel (b)
ax = axes[1]
ax.axhspan(GROUND - 0.55, GROUND, color="#e8edf4", zorder=0)
ax.plot([-4.6, 4.6], [GROUND, GROUND], color="#334155", lw=3, zorder=2)
ax.add_patch(plt.Rectangle((-1.6, PALM_Y - 0.05), 3.2, 0.62, facecolor="#c7d2fe",
                           edgecolor="#4338ca", lw=1.6, zorder=4))
ax.text(0, PALM_Y + 0.26, "palm", ha="center", va="center", fontsize=10,
        color="#312e81")

for x0 in (-1.05, 1.05):
    p2 = draw_leg(ax, x0, PALM_Y, A1, A2, "#1d4ed8")
    ax.plot(p2[0], p2[1], "o", ms=11, color="#1d4ed8", zorder=6)

# 摆动腿：关节摆开 → 脚尖抬离地面
SW1, SW2 = 0.95, -0.85
p2 = draw_leg(ax, 0.25, PALM_Y, SW1, SW2, "#f59e0b", alpha=0.55, zorder=3)
ax.plot(p2[0], p2[1], "o", ms=10, mfc="none", mec="#d97706", mew=2.2, zorder=6)
ax.annotate("", xy=(p2[0] + 0.05, p2[1] - 0.95), xytext=(p2[0] + 0.05, p2[1] - 0.28),
            arrowprops=dict(arrowstyle="-|>", color="#d97706", lw=2.6,
                            mutation_scale=20))
ax.annotate("", xy=(p2[0] + 0.05, p2[1] - 0.95), xytext=(p2[0] - 0.95, p2[1] - 0.95),
            arrowprops=dict(arrowstyle="-|>", color="#d97706", lw=2.6,
                            mutation_scale=20))
ax.text(2.55, p2[1] - 0.35, "摆动腿抬起\n不产生推力", fontsize=9.5,
        color="#b45309", ha="center", weight="bold")

ax.text(0, 2.05, "一个周期 = 支撑相推的那一下", fontsize=11.5, color="#0f172a",
        ha="center", weight="bold")
ax.text(0, 1.55, "摆动相净贡献 ≈ 0", fontsize=10, color="#b45309", ha="center")

ax.text(0.3, GROUND - 1.28,
        r"$\Delta x_{\rm cycle} = \sum_{\rm stance} v_{\rm body}\,\Delta t$",
        fontsize=13, color="#0f172a", ha="center",
        bbox=dict(boxstyle="round,pad=0.4", fc="#fff", ec="#94a3b8"))
ax.text(0.3, GROUND - 2.12, "所以「抬不抬得起脚」决定一切", fontsize=10.5,
        color="#475569", ha="center")

ax.set_title("② 摆动相：脚动 → 身体不动", fontsize=13, weight="bold", pad=8)
ax.set_xlim(-4.6, 4.6)
ax.set_ylim(GROUND - 2.7, 2.5)
ax.axis("off")

fig.savefig(os.path.join(FIG, "fig_p2_anchor.png"), dpi=170, bbox_inches="tight")
plt.close(fig)
print("wrote fig_p2_anchor.png")

# ======================================================== fig P3: 摔倒时间线
# 实测采样（residual_last.zip, seed 0, 每 25 步 = 0.05 s）
T = np.array([0.00, 0.09, 0.17, 0.26, 0.34, 0.43, 0.52])
X = np.array([0.64, 1.26, 3.08, 4.82, 6.15, 7.68, 10.00])
UP = np.array([1.00, 1.00, 0.97, 0.93, 0.89, 0.83, 0.696])
EDGE = 4.51        # 支撑边界（初始姿态实测 XMAX, cm）
UP_EDGE = np.cos(np.radians(25.3))   # 静态翻倒角对应的 up_z
UP_DEAD = 0.70

fig, axes = plt.subplots(1, 2, figsize=(13.2, 4.5))
fig.subplots_adjust(wspace=0.22)

# ---------------------------------------------------------------- 左：漂移
ax = axes[0]
tt = np.linspace(0, 0.52, 300)
xx = np.interp(tt, T, X)
ax.plot(tt, xx, lw=3, color="#dc2626", zorder=4)
ax.fill_between([0, 0.52], EDGE, 11.5, color="#fecaca", alpha=.55, zorder=0)
ax.axhline(EDGE, ls="--", lw=1.8, color="#b91c1c", zorder=3)
ax.text(0.015, EDGE + 0.35, "支撑边界 %.2f cm" % EDGE, fontsize=9.5,
        color="#b91c1c", weight="bold")

for t, x, lab in [(0.00, 0.64, "t=0\nup 1.00"), (0.34, 6.15, "越过边界\nup 0.89"),
                  (0.52, 10.00, "判摔\nup 0.70")]:
    ax.plot(t, x, "o", ms=8, color="#7f1d1d", zorder=6)
    ax.annotate(lab, (t, x), textcoords="offset points", xytext=(8, -22),
                fontsize=9, color="#7f1d1d", weight="bold")

ax.plot(0.17, 3.08, "o", ms=6, mfc="none", mec="#7f1d1d", mew=1.6, zorder=6)
ax.text(0.175, 1.05, "开始倾斜", fontsize=8.5, color="#7f1d1d")

ax.annotate("漂移 18 cm/s\n（前进只有 4.6 cm/s）", xy=(0.40, 7.3), xytext=(0.14, 8.6),
            fontsize=9.5, color="#dc2626", weight="bold",
            arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.4))
ax.set_xlim(0, 0.55)
ax.set_ylim(0, 11.5)
ax.set_xlabel("time (s)", fontsize=10)
ax.set_ylabel("侧向位移 X (cm)", fontsize=10)
ax.set_title("① 侧向漂移：0.34 s 越界", fontsize=13, weight="bold", pad=8)
ax.grid(alpha=.25)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

# ---------------------------------------------------------------- 右：倾角
ax = axes[1]
ax.plot(tt, np.interp(tt, T, UP), lw=3, color="#2563eb", zorder=4)
ax.axhline(UP_EDGE, ls="--", lw=1.8, color="#b91c1c", zorder=3)
ax.axhline(UP_DEAD, ls="--", lw=1.8, color="#6b7280", zorder=3)
ax.fill_between([0, 0.55], UP_DEAD, UP_EDGE, color="#fee2e2", alpha=.7, zorder=0)
ax.text(0.012, UP_EDGE + 0.012, "静态翻倒 25.3°（物理上已经倒了）",
        fontsize=9, color="#b91c1c", weight="bold")
ax.text(0.012, UP_DEAD + 0.012, "判摔阈值 up_z>0.70 = 45.6°", fontsize=9,
        color="#4b5563", weight="bold")
ax.text(0.30, (UP_EDGE + UP_DEAD) / 2, "死区 0.18 s\n环境还在给 alive 奖励",
        fontsize=9.5, color="#b91c1c", ha="center", va="center", weight="bold")
ax.axvspan(0.34, 0.52, color="#fecaca", alpha=.35, zorder=1)

ax.plot(0.34, 0.89, "o", ms=8, color="#1e3a8a", zorder=6)
ax.plot(0.52, 0.696, "o", ms=8, color="#1e3a8a", zorder=6)
ax.annotate("越界", (0.34, 0.89), textcoords="offset points", xytext=(-4, 12),
            fontsize=9, color="#1e3a8a", ha="center", weight="bold")
ax.annotate("terminated", (0.52, 0.696), textcoords="offset points", xytext=(-6, -18),
            fontsize=9, color="#1e3a8a", ha="right", weight="bold")

ax.set_xlim(0, 0.55)
ax.set_ylim(0.66, 1.03)
ax.set_xlabel("time (s)", fontsize=10)
ax.set_ylabel(r"$up_z = R[2,0]$", fontsize=11)
ax.set_title("② 倾角：物理 25° 就倒了，46° 才判", fontsize=13, weight="bold", pad=8)
ax.grid(alpha=.25)
for s in ("top", "right"):
    ax.spines[s].set_visible(False)

fig.savefig(os.path.join(FIG, "fig_p3_fall.png"), dpi=170, bbox_inches="tight")
plt.close(fig)
print("wrote fig_p3_fall.png")
