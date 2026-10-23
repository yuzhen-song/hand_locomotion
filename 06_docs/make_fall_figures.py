"""Figures that explain the fall itself.

fig_f1  出界不等于摔倒：同一条裕度曲线，一个回来了，一个没有
fig_f2  倾覆力学：CoM 投影越过支撑边缘之后，重力矩把身体推倒
fig_f3  实际摔倒的四帧（bias = -0.40）
fig_f4  倾斜角按 cosh(wt) 发散：为什么 0.1 s 能救回来、0.25 s 就救不回来
"""

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import FancyArrowPatch, Polygon as MplPolygon, Wedge

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01_env"))
import stability as S  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "06_docs", "figs")
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
if os.path.exists(FONT):
    fm.fontManager.addfont(FONT)
plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams.update({"figure.dpi": 130, "axes.grid": True, "grid.alpha": 0.3})

print("good run ...", flush=True)
good = S.run(steps=10000, every=2)
print("falling run ...", flush=True)
bad = S.run(bias=-0.40, steps=1200, every=1)


def series(r, key, cast=float):
    return np.array([cast(v) if v is not None else np.nan for v in r[key]])


mg, mb = series(good, "marg"), series(bad, "marg")
tg, tb = np.array(good["t"]), np.array(bad["t"])

# ------------------------------------------------------------------ fig_f1
fig, axes = plt.subplots(2, 1, figsize=(8.6, 5.0))
ax = axes[0]
ax.plot(tg, mg, lw=0.9, color="tab:green")
ax.axhline(0, color="k", lw=1.2)
ax.fill_between(tg, mg, 0, where=(mg < 0), color="tab:green", alpha=0.3)
ax.set_title("① 正常行走：重心出界了，但 0.1 s 内被下一组接触拉回来（出界占 6%）",
             fontsize=10)
ax.set_ylabel("CoM 裕度 (cm)")
ax.set_xlim(2, 6)
ax.annotate("出界", xy=(3.05, -2), xytext=(3.5, -7), fontsize=9, color="tab:green",
            arrowprops=dict(arrowstyle="->", color="tab:green"))

ax = axes[1]
ax.plot(tb, mb, lw=1.1, color="tab:red")
ax.axhline(0, color="k", lw=1.2)
ax.fill_between(tb, mb, 0, where=(mb < 0), color="tab:red", alpha=0.3)
ax.axvline(bad["fell"], color="k", ls="--", lw=1.5)
ax.text(bad["fell"] + 0.02, np.nanmax(mb) * 0.7, "判定摔倒 %.2fs" % bad["fell"], fontsize=9)
ax.set_title("② bias = -0.40：出界之后一路走低，再也回不来（出界占 62%）", fontsize=10)
ax.set_xlabel("时间 (s)")
ax.set_ylabel("CoM 裕度 (cm)")
fig.suptitle("同一套判据、同一个机构：区别不在“有没有出界”，而在“出界之后回不回得来”",
             fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_f1_out_vs_fall.png"))
plt.close(fig)

# ------------------------------------------------------------------ fig_f2
fig, axes = plt.subplots(1, 3, figsize=(11.4, 3.8))
EDGE_X = 0.0


def draw_body(ax, com_x, tilt=0.0, label="", note=""):
    L = 3.2
    cx = com_x
    # support edge at EDGE_X, ground
    ax.axhline(0, color="0.35", lw=2)
    ax.plot([EDGE_X], [0], "o", ms=9, color="tab:blue")
    ax.plot([-2.2, 2.2], [0, 0], "-", color="tab:blue", lw=5, alpha=0.35)
    # body as a tilted stick from the edge to the CoM
    ang = math.pi / 2 + tilt
    topx = EDGE_X + L * math.cos(ang)
    topy = L * math.sin(ang)
    ax.plot([EDGE_X, topx], [0, topy], "-", lw=4, color="0.6", solid_capstyle="round")
    ax.plot(topx, topy, "o", ms=11, color="crimson")
    ax.annotate("CoM", (topx, topy), textcoords="offset points", xytext=(6, 4), fontsize=9,
                color="crimson")
    # gravity and reaction
    ax.add_patch(FancyArrowPatch((topx, topy), (topx, topy - 1.3), arrowstyle="-|>",
                                 mutation_scale=13, color="crimson", lw=1.8))
    ax.text(topx + 0.1, topy - 1.6, "mg", fontsize=9, color="crimson")
    ax.plot([topx, topx], [0, topy], ":", color="crimson", lw=1.0)
    ax.set_xlim(-2.6, 3.4)
    ax.set_ylim(-0.6, 4.0)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    ax.set_title(label, fontsize=10)
    ax.text(0.5, -0.10, note, transform=ax.transAxes, ha="center", va="top", fontsize=8.5)


draw_body(axes[0], -0.7, 0.0, "① 稳定",
          "CoM 投影落在支撑面内\n反力可以移到 CoM 正下方，力矩为 0")
draw_body(axes[1], 0.0, 0.0, "② 临界",
          "CoM 投影正好在边缘上\n反力作用在边缘，力矩恰好为 0")
draw_body(axes[2], 0.85, 0.42, "③ 倾覆",
          "CoM 投影越过边缘\n重力矩 M = mg·d 绕边缘把身体推倒")
axes[2].annotate("", xy=(EDGE_X + 0.75, 0.35), xytext=(EDGE_X + 0.05, 0.05),
                 arrowprops=dict(arrowstyle="-|>", color="tab:orange", lw=2.4,
                                 connectionstyle="arc3,rad=-0.45"))
axes[2].text(EDGE_X + 0.55, 0.75, "$\\ddot\\theta > 0$\n越倒越快", fontsize=8.5, color="tab:orange")
fig.suptitle("倾覆力学：质心投影越过支撑边缘的那一刻，重力矩由“被平衡”变成“加速”",
             fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_f2_tipping.png"))
plt.close(fig)

# ------------------------------------------------------------------ fig_f3
fig, axes = plt.subplots(1, 4, figsize=(12.8, 3.6))
want = (0.30, 0.50, 0.62, 0.70)
for ax, wt in zip(axes, want):
    i = int(np.argmin(np.abs(tb - wt)))
    poly = bad["poly"][i]
    com = bad["com"][i]
    if len(poly) >= 3:
        ax.add_patch(MplPolygon(poly, closed=True, fc="#cfe3ff", ec="tab:blue", lw=1.4,
                                alpha=0.85))
    elif len(poly) == 2:
        ax.plot(poly[:, 0], poly[:, 1], "-", color="tab:blue", lw=3)
    for p in poly:
        ax.plot(p[0], p[1], "o", ms=4, color="tab:blue")
    ax.plot(com[0], com[1], "x", ms=12, mew=2.8, color="crimson")
    # trail of the CoM
    j0 = max(0, i - 60)
    tr = np.array(bad["com"][j0:i + 1])
    ax.plot(tr[:, 0], tr[:, 1], "-", color="crimson", lw=1.0, alpha=0.5)
    mg_i = bad["marg"][i]
    ax.set_title("t = %.2f s　裕度 %s" % (tb[i], ("%+.2f cm" % mg_i) if np.isfinite(mg_i)
                                          else "无支撑"), fontsize=9.5)
    ax.set_aspect("equal")
    ax.set_xlim(-1, 11)
    ax.set_ylim(-11, 6)
    ax.tick_params(labelsize=7)
    if i == 0:
        ax.set_ylabel("Y (cm)", fontsize=8)
    ax.set_xlabel("X (cm)", fontsize=8)
fig.suptitle("实际摔倒过程（bias = -0.40）：红×是质心投影，它一路向 +X 漂，蓝色支撑面跟不上",
             fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_f3_fall_frames.png"))
plt.close(fig)

# ------------------------------------------------------------------ fig_f4
w = math.sqrt(981 / 10.5)
fig, ax = plt.subplots(figsize=(7.2, 3.6))
tt = np.linspace(0, 0.45, 300)
for t_out, c in zip((0.10, 0.15, 0.22, 0.30),
                    ("tab:green", "tab:olive", "tab:orange", "tab:red")):
    tt2 = tt[tt <= t_out]
    ax.plot(tt2, np.cosh(w * tt2), lw=2, color=c,
            label="出界 %.2f s" % t_out)
    ax.plot([t_out], [math.cosh(w * t_out)], "o", ms=7, color=c)
ax.axhline(1.5, color="k", ls=":", lw=1.2)
ax.text(0.30, 1.56, "倾斜超过 1.5 倍初始角 → 摆动腿来不及落地", fontsize=8.5)
ax.axvline(1 / w, color="0.4", ls="--", lw=1.2)
ax.text(1 / w + 0.005, 0.25, "$1/\\omega=0.103$ s", fontsize=8.5, rotation=90, color="0.35")
ax.set_xlabel("出界后经过的时间 (s)")
ax.set_ylabel("倾斜角放大倍数  $\\theta(t)/\\theta_0$")
ax.set_title("倾覆是不稳定平衡：$\\theta(t)=\\theta_0\\cosh(\\omega t)$，$\\omega=\\sqrt{g/h}=%.1f$ rad/s" % w, fontsize=10)
ax.legend(fontsize=8)
ax.set_ylim(0.9, 4.2)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_f4_cosh.png"))
plt.close(fig)


# ------------------------------------------------------------------ fig_f5
def rel_phase(r):
    t = np.array(r["t"])
    com = np.array(r["com"], dtype=float)
    off, vel = [], []
    for i, poly in enumerate(r["poly"]):
        if len(poly) < 3:
            off.append(np.nan)
            vel.append(np.nan)
            continue
        c = poly.mean(axis=0)
        off.append(com[i, 0] - c[0])
    off = np.array(off)
    vel = np.gradient(off, t)
    return t, off, vel


fig, axes = plt.subplots(1, 2, figsize=(10.6, 4.0))
for ax, r, name, col in ((axes[0], good, "调好的配置（活下来）", "tab:green"),
                         (axes[1], bad, "bias = -0.40（摔）", "tab:red")):
    t, off, vel = rel_phase(r)
    ok = np.isfinite(off)
    ax.plot(off[ok], vel[ok], lw=0.8, color=col, alpha=0.85)
    ax.plot(off[ok][0], vel[ok][0], "o", ms=8, color="k")
    ax.axvline(0, color="k", lw=0.8)
    ax.axvline(6.3, color="tab:blue", ls="--", lw=1.3)
    ax.axvline(-6.3, color="tab:blue", ls="--", lw=1.3)
    ax.set_xlim(-12, 12)
    ax.set_ylim(-25, 25)
    ax.set_xlabel("CoM 相对支撑多边形中心的横向偏移 (cm)")
    ax.set_ylabel("横向速度 (cm/s)")
    ax.set_title(name, fontsize=10)
    ax.text(6.5, 18, "支撑面边缘", fontsize=8, color="tab:blue")
axes[0].text(-11, -21, "轨迹被限制在中间：\n每个周期都回到 0 附近 → 稳定极限环",
             fontsize=8.5, color="tab:green")
axes[1].text(-11, -21, "轨迹一路向右上方跑：\n偏移和速度同号 → 正反馈发散",
             fontsize=8.5, color="tab:red")
fig.suptitle("相图：横轴是“偏了多少”，纵轴是“还在往那边跑多快”——同号就是越跑越远",
             fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_f5_phase.png"))
plt.close(fig)

print("saved fig_f1 .. fig_f5")

def longest(t, m):
    best = cur = 0.0
    for i in range(1, len(m)):
        if m[i] < 0:
            cur += t[i] - t[i - 1]
            best = max(best, cur)
        else:
            cur = 0.0
    return best
print("good: 出界 %.0f%%, 单次最长 %.2fs" % (np.mean(mg < 0) * 100, longest(tg, mg)))
print("bad : 出界 %.0f%%, 单次最长 %.2fs, 摔于 %.2fs" % (np.mean(mb < 0) * 100, longest(tb, mb), bad["fell"]))
