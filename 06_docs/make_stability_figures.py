"""Figures for 06_docs/stability_analysis.md.

fig_s1  static margin over time, crawl vs trot
fig_s2  support polygon + CoM projection + ZMP at four moments
fig_s3  the four ways it falls, with the margin trace and the fall marked
fig_s4  fall boundary over knee and over bias
"""

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MplPolygon

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

print("running crawl ...", flush=True)
crawl = S.run("crawl", knee=0.0, steps=6000, open_loop=True, every=5)
print("running trot ...", flush=True)
trot = S.run("trot", steps=12000, every=5)


def marg(r):
    return np.array(r["marg"], dtype=float)


# ------------------------------------------------------------------ fig_s1
fig, axes = plt.subplots(2, 1, figsize=(8.4, 4.8), sharex=False)
for ax, r, name, col in ((axes[0], crawl, "3&1 爬行（开环）", "tab:blue"),
                         (axes[1], trot, "2&2 对角（当前配置）", "tab:green")):
    m = marg(r)
    t = r["t"]
    ax.plot(t, m, lw=1.0, color=col)
    ax.axhline(0, color="k", lw=1.2)
    if (m < 0).any():
        ax.fill_between(t, m, 0, where=(m < 0), color="tab:red", alpha=0.35,
                        label="CoM 跑出支撑多边形")
    ax.set_ylabel("静态裕度 (cm)")
    ax.set_title("%s：平均 %+.2f cm，最小 %+.2f cm" % (name, np.nanmean(m), np.nanmin(m)),
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower left")
axes[1].set_xlabel("时间 (s)")
fig.suptitle("静态稳定裕度 = CoM 投影到支撑多边形边界的有符号距离（负 = 已经出界）",
             fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_s1_margin_time.png"))
plt.close(fig)

# ------------------------------------------------------------------ fig_s2
fig, axes = plt.subplots(2, 4, figsize=(12.6, 6.4))
for row, (r, name) in enumerate(((crawl, "3&1 爬行"), (trot, "2&2 对角"))):
    n = len(r["t"])
    idx = [int(n * f) for f in (0.10, 0.18, 0.26, 0.34)]
    for col, i in enumerate(idx):
        ax = axes[row, col]
        poly = r["poly"][i]
        com = r["com"][i]
        zm = r["zmp"][i]
        if len(poly) >= 3:
            ax.add_patch(MplPolygon(poly, closed=True, fc="#cfe3ff", ec="tab:blue",
                                    lw=1.4, alpha=0.85))
        elif len(poly) == 2:
            ax.plot(poly[:, 0], poly[:, 1], "-", color="tab:blue", lw=2.5)
        for p in poly:
            ax.plot(p[0], p[1], "o", ms=5, color="tab:blue")
        ax.plot(com[0], com[1], "x", ms=11, mew=2.6, color="crimson")
        if np.isfinite(zm).all():
            ax.plot(zm[0], zm[1], "^", ms=8, color="darkorange")
        mg = r["marg"][i]
        ax.set_title("t=%.2fs  裕度 %+.2fcm" % (r["t"][i], mg), fontsize=9)
        ax.set_aspect("equal")
        ax.set_xlim(com[0] - 13, com[0] + 13)
        ax.set_ylim(com[1] - 13, com[1] + 13)
        ax.tick_params(labelsize=7)
        if col == 0:
            ax.set_ylabel(name + "\nY (cm)", fontsize=9)
        else:
            ax.set_yticks([])
        if row == 1:
            ax.set_xlabel("X (cm)", fontsize=8)
fig.suptitle("支撑多边形（蓝）· CoM 投影（红×）· ZMP（橙三角）　"
             "上行：三脚架支撑；下行：对角两点，多边形退化成一条线", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_s2_polygon.png"))
plt.close(fig)

# ------------------------------------------------------------------ fig_s3
CASES = [
    ("bias = -0.40（横向驱动过强）", dict(gait_name="trot", bias=-0.40, steps=6000)),
    ("stride = 1.0（步幅过大）", dict(gait_name="trot", stride=1.0, steps=16000)),
    ("knee = 1.0（抬腿很高，但能救回来）", dict(gait_name="trot", knee=1.0, steps=12000)),
    ("调好的配置（bias -0.10 / yaw -0.20）", dict(gait_name="trot", steps=12000)),
]
fig, axes = plt.subplots(2, 2, figsize=(10.4, 5.6))
info = []
for ax, (label, kw) in zip(axes.ravel(), CASES):
    print("case:", label, flush=True)
    r = S.run(**kw)
    m = marg(r)
    t = r["t"]
    ax.plot(t, m, lw=1.0, color="tab:purple")
    ax.axhline(0, color="k", lw=1.1)
    frac = np.mean(m < 0) * 100
    if r["fell"]:
        ax.axvline(r["fell"], color="tab:red", ls="--", lw=1.6)
        ax.set_title("%s\n摔于 %.2fs　出界占比 %.0f%%" % (label, r["fell"], frac), fontsize=9)
    else:
        ax.set_title("%s\n活下来　出界占比 %.0f%%" % (label, frac), fontsize=9)
    ax.set_xlabel("时间 (s)", fontsize=8)
    ax.set_ylabel("静态裕度 (cm)", fontsize=8)
    info.append((label, r["fell"], np.nanmin(m) if len(m) else np.nan, frac))
fig.suptitle("深不是问题，久才是问题：裕度跌到 -11 cm 也能活，出界时间一长就必倒", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_s3_falls.png"))
plt.close(fig)
for label, fell, mn, frac in info:
    print("   %-34s %s  最小裕度 %+.2f  出界 %.0f%%"
          % (label, ("摔于 %.2fs" % fell) if fell else "没摔", mn, frac))

# ------------------------------------------------------------------ fig_s4
print("sweeping knee ...", flush=True)
knees = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
kres = [(k, S.run("trot", knee=k, steps=8000)) for k in knees]
print("sweeping bias ...", flush=True)
biases = [-0.06, -0.10, -0.16, -0.24, -0.32, -0.40]
bres = [(b, S.run("trot", bias=b, steps=8000)) for b in biases]

fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.8))
for ax, data, lab in ((axes[0], kres, "knee（抬腿量, rad）"),
                      (axes[1], bres, "bias（步幅偏置）")):
    xs, mins, fell = [], [], []
    for x, r in data:
        m = marg(r)
        xs.append(x)
        mins.append(np.nanmin(m) if len(m) else np.nan)
        fell.append(r["fell"] is not None)
    ax.plot(xs, mins, "o-", color="tab:blue")
    for x, mn, f in zip(xs, mins, fell):
        if f:
            ax.plot(x, mn if np.isfinite(mn) else ax.get_ylim()[0], "x", ms=13,
                    mew=3, color="tab:red")
    ax.axhline(0, color="k", lw=1.1)
    ax.set_xlabel(lab)
    ax.set_ylabel("整段最小静态裕度 (cm)")
    ax.set_title("%s：红叉 = 该参数下摔倒" % lab.split("（")[0], fontsize=10)
fig.suptitle("稳定边界：裕度跌破 0 之后还能撑一会儿，再往下就摔", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_s4_boundary.png"))
plt.close(fig)

for k, r in kres:
    print("  knee %.1f -> %s, 最小裕度 %+.2f" % (k, "FELL" if r["fell"] else "ok",
                                                 np.nanmin(marg(r))))
for b, r in bres:
    print("  bias %+.2f -> %s, 最小裕度 %+.2f" % (b, "FELL" if r["fell"] else "ok",
                                                 np.nanmin(marg(r))))
print("done")
