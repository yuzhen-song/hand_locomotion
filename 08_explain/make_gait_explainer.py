"""Build the explainer video: what the gait actually does, frame by frame.

Panels
  left   top view, the fingers drawn as polylines, stance tips filled and
         anchored, swing tips hollow and lifted, a scrolling ruler
  right  side view (Y-Z) so the lift is visible, the phase timeline with a
         playhead, and a live formula box
  bottom a caption strip that walks through the six ideas

Output: 05_videos/gait_explainer.mp4 (+ .gif)
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
from matplotlib.patches import FancyBboxPatch, Polygon

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01_env"))
import mujoco  # noqa: E402

from controller import TrotController  # noqa: E402
from gait import PHASE_SETS  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
if os.path.exists(FONT):
    fm.fontManager.addfont(FONT)
plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

FPS = 20
DUR = 30.0
DT = 0.002
EVERY = int(1.0 / (FPS * DT))

m = mujoco.MjModel.from_xml_path(os.path.join(ROOT, "03_model", "quadruped_sim.xml"))
d = mujoco.MjData(m)
JN = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, i) for i in range(m.njnt)]
ORDER = [n for n in JN if n and "unit" in n]
ACTS = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]
LUT = {n.replace("m_", ""): i for i, n in enumerate(ACTS)}
ABD0 = {"C": 0.63, "A": -0.63, "B": 0.63, "D": -0.63}
Q0 = np.array([{"MCP-FLX": -1.10, "MCP-ABD": ABD0[n.split("-")[0].replace("unit", "")],
                "PIP": 1.60, "DIP": -0.35}[n.split("-", 1)[1]] for n in ORDER])
LEGS = "ABCD"
CHAIN = {lg: ["unit%s-MCP-ABD" % lg, "unit%s-MCP-FLX" % lg,
              "unit%s-PIP" % lg, "unit%s-DIP" % lg] for lg in LEGS}
JID = {n: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n) for n in ORDER}
TIPB = {"C": "finger_tip", "A": "finger_tip_2", "B": "finger_tip_3", "D": "finger_tip_4"}
COL = {"A": "#1f77b4", "B": "#ff7f0e", "C": "#2ca02c", "D": "#d62728"}
PERIOD, DUTY = 1.6, 0.5
PH = PHASE_SETS["trot"]


def pd(targets):
    u = np.zeros(m.nu)
    q = d.qpos[7:].copy()
    qd = d.qvel[6:].copy()
    for k, n in enumerate(ORDER):
        u[LUT[n]] = 40.0 * (targets[k] - q[k]) - 4.0 * qd[k]
    d.ctrl[:] = np.clip(u, -10, 10)


print("running the simulation ...", flush=True)
mujoco.mj_resetData(m, d)
d.qpos[2] = 0.14
d.qpos[7:] = Q0
mujoco.mj_forward(m, d)
for _ in range(400):
    pd(Q0)
    mujoco.mj_step(m, d)

ctl = TrotController(ORDER, Q0)
ctl.reset(float(d.qpos[0]), float(d.qpos[1]))
y_start = float(d.qpos[1])

frames = []
t = 0.0
for st in range(int(DUR / DT)):
    t += DT
    pd(ctl.targets(t, d.qpos, DT))
    mujoco.mj_step(m, d)
    if st % EVERY:
        continue
    body = np.array(d.body("platform_mount").xpos) * 100
    R = np.array(d.body("platform_mount").xmat).reshape(3, 3)
    yaw = math.atan2(R[1, 0], R[0, 0])
    poly = {}
    for lg in LEGS:
        pts = [np.array(d.xanchor[JID[j]]) * 100 for j in CHAIN[lg]]
        pts.append(np.array(d.body(TIPB[lg]).xpos) * 100)
        poly[lg] = np.array(pts)
    phases = {lg: (t / PERIOD + PH[lg]) % 1.0 for lg in LEGS}
    frames.append(dict(t=t, body=body, yaw=yaw, poly=poly, phases=phases))
print("frames captured:", len(frames), flush=True)

# ---------------------------------------------------------------- the figure
fig = plt.figure(figsize=(11.6, 6.6), dpi=110)
gs = fig.add_gridspec(3, 2, width_ratios=[1.15, 1.0], height_ratios=[1.0, 0.62, 0.24],
                      left=0.055, right=0.975, top=0.93, bottom=0.05,
                      wspace=0.16, hspace=0.42)
ax_top = fig.add_subplot(gs[:, 0])
ax_side = fig.add_subplot(gs[0, 1])
ax_phase = fig.add_subplot(gs[1, 1])
ax_eq = fig.add_subplot(gs[2, 1])
ax_cap = fig.add_axes([0.055, 0.005, 0.92, 0.058])
for a in (ax_cap,):
    a.axis("off")

fig.suptitle("四指手 · 2&2 对角步态是怎么走的", fontsize=14, y=0.975)

# top view static bits
ax_top.set_aspect("equal")
ax_top.set_xlabel("X (cm)  ← 横向 →")
ax_top.set_ylabel("Y (cm)  前进方向 →")
ax_top.set_title("俯视图：实心=踩住地面，空心=抬脚前移", fontsize=10)
ax_top.grid(alpha=0.25)
line_body = Polygon(np.zeros((4, 2)), closed=True, fc="#ffe8e8", ec="crimson", lw=1.4)
ax_top.add_patch(line_body)
trail, = ax_top.plot([], [], "-", color="crimson", lw=1.0, alpha=0.35)
fingers = {lg: ax_top.plot([], [], "-", lw=2.2, color=COL[lg], solid_capstyle="round")[0]
           for lg in LEGS}
tips = {lg: ax_top.plot([], [], "o", ms=8, color=COL[lg])[0] for lg in LEGS}
head_arrow = ax_top.annotate("", xy=(0, 0), xytext=(0, 0),
                             arrowprops=dict(arrowstyle="-|>", color="crimson", lw=1.6))
ruler_lines, ruler_texts = [], []
for k in range(-4, 90, 10):
    ruler_lines.append(ax_top.plot([], [], "-", color="0.75", lw=0.8)[0])
    ruler_texts.append(ax_top.text(0, 0, "%+d" % k, fontsize=6.5, color="0.45",
                                   ha="right", va="center"))

# side view static bits
ax_side.set_title("侧视图：抬脚高度", fontsize=10)
ax_side.set_xlabel("Y (cm)")
ax_side.set_ylabel("Z (cm)")
ax_side.set_ylim(0, 16)
ax_side.grid(alpha=0.25)
side_f = {lg: ax_side.plot([], [], "-", lw=2.0, color=COL[lg])[0] for lg in LEGS}
side_t = {lg: ax_side.plot([], [], "o", ms=6, color=COL[lg])[0] for lg in LEGS}
side_ground = ax_side.axhline(0, color="0.4", lw=1.2)

# phase timeline, drawn once
ax_phase.set_title("相位：蓝=支撑，橙=摆动", fontsize=10)
ax_phase.set_xlim(-1.5, 3.2)
ax_phase.set_ylim(-0.6, 3.6)
ax_phase.set_yticks(range(4))
ax_phase.set_yticklabels(list(LEGS))
ax_phase.set_xlabel("周期数")
ax_phase.grid(alpha=0.2, axis="x")
for i, lg in enumerate(LEGS):
    for k in range(-1, 3):
        off = PH[lg] + k
        ax_phase.barh(i, DUTY, left=off, height=0.5, color="#4c72b0", alpha=0.85)
        ax_phase.barh(i, 1 - DUTY, left=off + DUTY, height=0.5, color="#dd8452", alpha=0.85)
playhead = ax_phase.axvline(0, color="k", lw=2)

ax_eq.axis("off")
eq_txt = ax_eq.text(0.0, 1.02, "", fontsize=9.5, va="top", family="monospace",
                    transform=ax_eq.transAxes)
cap_txt = ax_cap.text(0.0, 0.5, "", fontsize=12.5, va="center", color="#1a1a1a")

CAPTIONS = [
    (0.0, "① 这是一只手，也是四条腿：4 根手指 × 4 个关节 = 16 个伺服电机"),
    (4.5, "② 2&2 对角步态：A+D 一组，B+C 一组，永远有一组踩在地上"),
    (9.0, "③ 支撑相（蓝）：指尖踩住地面不动 → 身体被反推向前，这叫“锚定”"),
    (14.0, "④ 摆动相（橙）：指尖抬起 2cm、向前挪 → 为下一次蹬地做准备"),
    (19.5, "⑤ 每蹬一次身体就转一下（偏航 ±100°）：靠差动步幅自动阻尼"),
    (24.0, "⑥ 30 秒走 0.93 米：3.11 cm/s，横向只偏 6%"),
    (28.0, "完整过程：踩住 → 反推 → 抬起 → 前移 → 再踩住，循环往复"),
]

tmp = tempfile.mkdtemp(prefix="gaitexpl_")


def render(i, fr):
    t = fr["t"]
    body, yaw = fr["body"], fr["yaw"]
    poly = fr["poly"]
    ph = fr["phases"]

    # ---- top view
    half_l, half_w = 6.5, 9.5
    c, s = math.cos(yaw), math.sin(yaw)
    corners = np.array([[-half_l, -half_w], [half_l, -half_w],
                        [half_l, half_w], [-half_l, half_w]])
    rot = np.array([[c, -s], [s, c]])
    line_body.set_xy(corners @ rot.T + body[:2])
    n = max(2, i // 3)
    trail.set_data([f["body"][0] for f in frames[:n:2]], [f["body"][1] for f in frames[:n:2]])
    head_arrow.xy = (body[0] + 7 * math.sin(yaw), body[1] + 7 * math.cos(yaw))
    head_arrow.xytext = (body[0], body[1])
    for lg in LEGS:
        P = poly[lg]
        stance = ph[lg] < DUTY
        fingers[lg].set_data(P[:, 0], P[:, 1])
        tips[lg].set_data([P[-1, 0]], [P[-1, 1]])
        tips[lg].set_markerfacecolor(COL[lg] if stance else "white")
        tips[lg].set_markeredgewidth(2.0)
        tips[lg].set_markeredgecolor(COL[lg])
        tips[lg].set_markersize(9 if stance else 11)
    y_lo, y_hi = body[1] - 26, body[1] + 34
    ax_top.set_xlim(-19, 19)
    ax_top.set_ylim(y_lo, y_hi)
    for ln, tx, k in zip(ruler_lines, ruler_texts, range(-4, 90, 10)):
        yy = max(y_lo + 0.5, min(y_hi - 0.5, k))
        ln.set_data([-19, -18], [yy, yy])
        tx.set_position((-18.4, yy))
        tx.set_text("%+d" % k)

    # ---- side view
    for lg in LEGS:
        P = poly[lg]
        side_f[lg].set_data(P[:, 1], P[:, 2])
        side_t[lg].set_data([P[-1, 1]], [P[-1, 2]])
        stance = ph[lg] < DUTY
        side_t[lg].set_markerfacecolor(COL[lg] if stance else "white")
        side_t[lg].set_markeredgewidth(1.8)
        side_t[lg].set_markeredgecolor(COL[lg])
    ax_side.set_xlim(body[1] - 26, body[1] + 26)

    # ---- playhead
    playhead.set_xdata([t / PERIOD, t / PERIOD])

    st = {lg: (ph[lg] < DUTY) for lg in LEGS}
    lines = [
        "φi(t) = ( t/T + φi⁰ ) mod 1        T=1.6s",
        "",
        "支撑相 φ<0.5 :  指尖不动，v_body = -J q̇",
        "摆动相 φ≥0.5 :  q* = q0 + A sin2πφ + k·w",
        "",
        "  t = %5.2fs   φ_A=%.2f  φ_B=%.2f  φ_C=%.2f  φ_D=%.2f"
        % (t, ph["A"], ph["B"], ph["C"], ph["D"]),
        "  支撑: " + "  ".join("%s%s" % (lg, "✓" if st[lg] else "×") for lg in LEGS),
    ]
    eq_txt.set_text("\n".join(lines))

    cap = ""
    for t0, txt in CAPTIONS:
        if t >= t0:
            cap = txt
    cap_txt.set_text(cap)
    cap_txt.set_color("#0a3069")

    fig.savefig(os.path.join(tmp, "f%05d.png" % i))
    if i % 100 == 0:
        print("  frame %d / %d" % (i, len(frames)), flush=True)


print("rendering %d frames ..." % len(frames), flush=True)
for i, fr in enumerate(frames):
    render(i, fr)

out_dir = os.path.join(ROOT, "05_videos")
os.makedirs(out_dir, exist_ok=True)
out = os.path.join(out_dir, "gait_explainer.mp4")
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-framerate", str(FPS),
                "-i", os.path.join(tmp, "f%05d.png"),
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "23", out],
               check=True)
print("saved", out, flush=True)
shutil.rmtree(tmp, ignore_errors=True)
