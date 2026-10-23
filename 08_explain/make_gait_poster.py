"""A one-page poster: four snapshots through one trot cycle.

Saved to 06_docs/figs/fig11_gait_poster.png, meant to sit next to the explainer
video so the reader can see the four states without pressing play.
"""

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import Polygon

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
WANT = (0.0, 0.5, 0.8, 1.3)


def pd(targets):
    u = np.zeros(m.nu)
    q = d.qpos[7:].copy()
    qd = d.qvel[6:].copy()
    for k, n in enumerate(ORDER):
        u[LUT[n]] = 40.0 * (targets[k] - q[k]) - 4.0 * qd[k]
    d.ctrl[:] = np.clip(u, -10, 10)


mujoco.mj_resetData(m, d)
d.qpos[2] = 0.14
d.qpos[7:] = Q0
mujoco.mj_forward(m, d)
for _ in range(400):
    pd(Q0)
    mujoco.mj_step(m, d)
ctl = TrotController(ORDER, Q0)
ctl.reset(float(d.qpos[0]), float(d.qpos[1]))

shots = []
t = 0.0
nxt = 0
while nxt < len(WANT):
    t += 0.002
    pd(ctl.targets(t, d.qpos, 0.002))
    mujoco.mj_step(m, d)
    if t >= 3.0 + WANT[nxt]:
        out = {"t": t, "ph": {lg: (t / PERIOD + PH[lg]) % 1.0 for lg in LEGS}}
        out["poly"] = {lg: np.array([np.array(d.xanchor[JID[j]]) * 100 for j in CHAIN[lg]]
                                    + [np.array(d.body(TIPB[lg]).xpos) * 100]) for lg in LEGS}
        R = np.array(d.body("platform_mount").xmat).reshape(3, 3)
        out["body"] = np.array(d.body("platform_mount").xpos) * 100
        out["yaw"] = math.atan2(-R[0, 1], R[1, 1])
        shots.append(out)
        nxt += 1

NOTE = [
    ("t = 0.0 s", "A+D 正在踩着地面（实心），\nB+C 抬脚前移（空心）"),
    ("t = 0.5 s", "对角换脚：B+C 落地，\nA+D 离地抬起"),
    ("t = 0.8 s", "A+D 在空中前移 4~8 cm，\nB+C 单组支撑推着身体走"),
    ("t = 1.3 s", "A+D 即将落地，\n一个周期走 4.78 cm"),
]

fig, axes = plt.subplots(1, 4, figsize=(13.2, 4.3), dpi=120)
for ax, sh, note in zip(axes, shots, NOTE):
    body, yaw, poly, ph = sh["body"], sh["yaw"], sh["poly"], sh["ph"]
    c, s = math.cos(yaw), math.sin(yaw)
    corners = np.array([[-6.5, -9.5], [6.5, -9.5], [6.5, 9.5], [-6.5, 9.5]])
    ax.add_patch(Polygon(corners @ np.array([[c, -s], [s, c]]).T + body[:2],
                         closed=True, fc="#ffe8e8", ec="crimson", lw=1.3))
    for lg in LEGS:
        P = poly[lg]
        stance = ph[lg] < DUTY
        ax.plot(P[:, 0], P[:, 1], "-", lw=2.4, color=COL[lg], solid_capstyle="round",
                alpha=1.0 if stance else 0.42)
        ax.plot([P[-1, 0]], [P[-1, 1]], "o", ms=11,
                mfc=COL[lg] if stance else "white", mec=COL[lg], mew=2.2)
    ax.set_xlim(body[0] - 17, body[0] + 17)
    ax.set_ylim(body[1] - 17, body[1] + 17)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(alpha=0.15)
    ax.set_title(note[0], fontsize=10)
    ax.text(0.5, -0.13, note[1], transform=ax.transAxes, ha="center", va="top",
            fontsize=9, color="#333")

fig.suptitle("一个周期内的四个状态（俯视）　实心＝支撑相（踩住不动）　空心＝摆动相（抬脚前移）",
             fontsize=12, y=0.99)
fig.text(0.5, 0.055,
         "支撑相：v_body = −J q̇　（指尖不动 → 身体被反推）　　摆动相：q* = q₀ + A sin 2πφ + k·w(φ)",
         ha="center", fontsize=10.5, color="#0a3069")
fig.subplots_adjust(left=0.03, right=0.98, top=0.80, bottom=0.16, wspace=0.12)
out = os.path.join(ROOT, "06_docs", "figs", "fig11_gait_poster.png")
fig.savefig(out)
print("saved", out)
