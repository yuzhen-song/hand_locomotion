"""Slow-motion video of the bias = -0.40 fall.

0.52 s of simulation stretched to about 4 s (8x slow motion) so the CoM can be
watched leaving the support polygon.  Left: top view with the support polygon,
the contact points, the fingers and the CoM trail.  Right: the tilt angle
against time, with the cosh envelope for reference.

Output: 05_videos/fall_explainer.mp4 (+ .gif)
"""

import math
import os
import shutil
import subprocess
import sys
import tempfile

import imageio_ffmpeg
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon as MplPolygon

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01_env"))
import mujoco  # noqa: E402

from controller import TrotController  # noqa: E402
from gait import heading_of  # noqa: E402
import stability as S  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
if os.path.exists(FONT):
    fm.fontManager.addfont(FONT)
plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
LEGS = "ABCD"
CHAIN = {lg: ["unit%s-MCP-ABD" % lg, "unit%s-MCP-FLX" % lg,
              "unit%s-PIP" % lg, "unit%s-DIP" % lg] for lg in LEGS}
TIPB = {"C": "finger_tip", "A": "finger_tip_2", "B": "finger_tip_3", "D": "finger_tip_4"}
COL = {"A": "#1f77b4", "B": "#ff7f0e", "C": "#2ca02c", "D": "#d62728"}
T0, T1 = 0.26, 0.80
NFRAMES = 84

print("running the falling case ...", flush=True)
m, d, order, lut, q0, tipbody = S.make()
jids = {n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n) for n in order}
ctl = TrotController(order, q0, bias=-0.40)
mujoco.mj_resetData(m, d)
d.qpos[2] = 0.14
d.qpos[7:] = q0
mujoco.mj_forward(m, d)
for _ in range(400):
    S.pd(m, d, order, lut, q0)
    mujoco.mj_step(m, d)
ctl.reset(float(d.qpos[0]), float(d.qpos[1]))

rec = []
t = 0.0
while t < T1 + 0.05:
    t += m.opt.timestep
    S.pd(m, d, order, lut, ctl.targets(t, d.qpos, m.opt.timestep))
    mujoco.mj_step(m, d)
    R = np.array(d.body("platform_mount").xmat).reshape(3, 3)
    com = np.array(d.subtree_com[0]) * 100
    pts, _ = S.contacts(m, d)
    poly = S.hull(pts) if len(pts) else np.zeros((0, 2))
    fingers = {lg: np.array([np.array(d.xanchor[jids[j]]) * 100 for j in CHAIN[lg]]
                            + [np.array(d.body(TIPB[lg]).xpos) * 100]) for lg in LEGS}
    rec.append(dict(t=t, com=com[:2], poly=poly, fing=fingers,
                    tilt=math.degrees(math.acos(np.clip(R[2, 0], -1, 1))),
                    marg=S.signed_margin(poly, com[:2]) if len(poly) else np.nan,
                    ncon=len(pts)))
print("recorded", len(rec), "samples", flush=True)

idx = [int(np.argmin(np.abs([r["t"] for r in rec] - v)))
       for v in np.linspace(T0, T1, NFRAMES)]

fig = plt.figure(figsize=(11.2, 5.4), dpi=110)
gs = fig.add_gridspec(2, 2, width_ratios=[1.35, 1.0], height_ratios=[1, 0.16],
                      left=0.05, right=0.98, top=0.90, bottom=0.04, wspace=0.16,
                      hspace=0.30)
ax = fig.add_subplot(gs[:, 0])
ax_t = fig.add_subplot(gs[0, 1])
ax_s = fig.add_subplot(gs[1, :])
for a in (ax_s,):
    a.axis("off")
fig.suptitle("慢放 8×：bias = -0.40 是怎么倒的　（红× = 质心投影，蓝 = 支撑多边形）",
             fontsize=12, y=0.965)

ax.set_aspect("equal")
ax.set_xlim(-2, 12)
ax.set_ylim(-12, 6)
ax.set_xlabel("X (cm)")
ax.set_ylabel("Y (cm)")
ax.grid(alpha=0.25)
poly_patch = MplPolygon(np.zeros((3, 2)), closed=True, fc="#cfe3ff", ec="tab:blue", lw=1.8)
ax.add_patch(poly_patch)
line_seg, = ax.plot([], [], "-", color="tab:blue", lw=3.5)
contact_dots, = ax.plot([], [], "o", ms=6, color="tab:blue")
fing_lines = {lg: ax.plot([], [], "-", lw=2.0, color=COL[lg], alpha=0.85)[0] for lg in LEGS}
trail, = ax.plot([], [], "-", color="crimson", lw=1.2, alpha=0.55)
com_dot, = ax.plot([], [], "x", ms=15, mew=3.2, color="crimson")
warn = ax.text(0.02, 0.97, "", transform=ax.transAxes, fontsize=12, va="top",
               color="crimson", fontweight="bold")

allt = np.array([r["t"] for r in rec])
alltilt = np.array([r["tilt"] for r in rec])
ax_t.plot(allt, alltilt, lw=0.9, color="0.7")
ax_t.set_xlim(T0, T1)
ax_t.set_ylim(0, max(60, alltilt.max() * 1.1))
ax_t.set_xlabel("时间 (s)", fontsize=8)
ax_t.set_ylabel("倾角 (°)", fontsize=8)
ax_t.set_title("倾角：越倒越快", fontsize=10)
tilt_dot, = ax_t.plot([], [], "o", ms=8, color="crimson")
tilt_vl = ax_t.axvline(T0, color="k", lw=1.0)
ax_t.grid(alpha=0.25)

status = ax_s.text(0.0, 0.5, "", fontsize=13, va="center", color="#0a3069")

tmp = tempfile.mkdtemp(prefix="fallvid_")
for i, j in enumerate(idx):
    r = rec[j]
    poly, com = r["poly"], r["com"]
    if len(poly) >= 3:
        poly_patch.set_xy(poly)
        poly_patch.set_visible(True)
        line_seg.set_data([], [])
    elif len(poly) == 2:
        poly_patch.set_visible(False)
        line_seg.set_data(poly[:, 0], poly[:, 1])
    else:
        poly_patch.set_visible(False)
        line_seg.set_data([], [])
    if len(poly):
        contact_dots.set_data(poly[:, 0], poly[:, 1])
    else:
        contact_dots.set_data([], [])
    for lg in LEGS:
        P = r["fing"][lg]
        fing_lines[lg].set_data(P[:, 0], P[:, 1])
    k0 = max(0, j - 90)
    tr = np.array([rec[q]["com"] for q in range(k0, j + 1)])
    trail.set_data(tr[:, 0], tr[:, 1])
    com_dot.set_data([com[0]], [com[1]])
    out = np.isfinite(r["marg"]) and r["marg"] < 0
    warn.set_text("质心已跑出支撑面！" if out else "")
    tilt_dot.set_data([r["t"]], [r["tilt"]])
    tilt_vl.set_xdata([r["t"], r["t"]])
    status.set_text(
        "t = %.2f s    裕度 %s    倾角 %4.1f°    接触点 %d"
        % (r["t"], ("%+.2f cm" % r["marg"]) if np.isfinite(r["marg"]) else "  无支撑 ",
           r["tilt"], r["ncon"]))
    fig.savefig(os.path.join(tmp, "f%04d.png" % i))
    if i % 20 == 0:
        print("  frame %d / %d" % (i, NFRAMES), flush=True)

out = os.path.join(ROOT, "05_videos", "fall_explainer.mp4")
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-framerate", "20",
                "-i", os.path.join(tmp, "f%04d.png"), "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-crf", "23", out], check=True)
print("saved", out, flush=True)
shutil.rmtree(tmp, ignore_errors=True)
