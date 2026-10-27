"""Figures and numbers for 06_docs/locomotion_theory.md.

Mirrors the two lecture slides (velocity Jacobian / workspace / condition
number, and floating-base Lagrangian dynamics / motor selection) but with the
numbers of this hand:

fig_t1  Jacobian: unit velocity circle -> velocity ellipse, home vs folded
fig_t2  workspace of one fingertip, coloured by the condition number
fig_t3  dynamics: inertia / bias terms, and the measured joint torque profile
fig_t4  trajectory: our sine + envelope vs a quintic with zero end velocity
"""

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import font_manager as fm
from matplotlib.patches import Ellipse, FancyArrowPatch

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01_env"))
import mujoco  # noqa: E402

from controller import TrotController  # noqa: E402
from gait import PHASE_SETS, _smooth  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "06_docs", "figs")
FONT = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
if os.path.exists(FONT):
    fm.fontManager.addfont(FONT)
plt.rcParams["font.sans-serif"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False
plt.rcParams.update({"figure.dpi": 130, "axes.grid": True, "grid.alpha": 0.3})

m = mujoco.MjModel.from_xml_path(os.path.join(ROOT, "03_model", "quadruped_sim.xml"))
d = mujoco.MjData(m)
JN = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, i) for i in range(m.njnt)]
ORDER = [n for n in JN if n and "unit" in n]
ACTS = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]
LUT = {n.replace("m_", ""): i for i, n in enumerate(ACTS)}
ABD0 = {"C": 0.63, "A": -0.63, "B": 0.63, "D": -0.63}
Q0 = np.array([{"MCP-FLX": -1.10, "MCP-ABD": ABD0[n.split("-")[0].replace("unit", "")],
                "PIP": 1.60, "DIP": -0.35}[n.split("-", 1)[1]] for n in ORDER])
LEG = "A"
FA = ["unit%s-MCP-FLX" % LEG, "unit%s-MCP-ABD" % LEG,
      "unit%s-PIP" % LEG, "unit%s-DIP" % LEG]
DOFS = [m.jnt_dofadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)] for n in FA]
RANGES = np.array([m.jnt_range[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)]
                   for n in FA])
TIPB = {"C": "finger_tip", "A": "finger_tip_2", "B": "finger_tip_3", "D": "finger_tip_4"}
BEAD_BODY = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, TIPB[LEG])
BEADS = [i for i in range(m.ngeom)
         if m.geom_bodyid[i] == BEAD_BODY and m.geom_type[i] == 4]


def contact_point():
    """World position of the grasp-bead centroid = the body-frame contact point."""
    return np.array([d.geom_xpos[i] for i in BEADS]).mean(axis=0)


def pose(q):
    mujoco.mj_resetData(m, d)
    d.qpos[2] = 0.14
    d.qpos[7:] = q
    mujoco.mj_forward(m, d)
    return contact_point()


def jac(q):
    """3x4 translational Jacobian of the contact point, cm/rad."""
    p = pose(q)
    jp = np.zeros((3, m.nv))
    jr = np.zeros((3, m.nv))
    mujoco.mj_jac(m, d, jp, jr, p, BEAD_BODY)
    return jp[:, DOFS] * 100, p


def qA(vals):
    q = Q0.copy()
    for n, v in zip(FA, vals):
        q[ORDER.index(n)] = v
    return q


J_home, p_home = jac(Q0)
J_fold, p_fold = jac(qA([-1.10, -0.63, 0.6, 0.0]))
print("=== Jacobian at home (cm/rad), columns = FLX, ABD, PIP, DIP ===")
print(np.round(J_home, 3))
S_home = np.linalg.svd(J_home, compute_uv=False)
S_fold = np.linalg.svd(J_fold, compute_uv=False)
print("singular values home:", np.round(S_home, 3),
      " kappa2 = %.2f" % (S_home[0] / S_home[1]))
print("singular values fold:", np.round(S_fold, 3),
      " kappa2 = %.2f" % (S_fold[0] / S_fold[1]))

# ------------------------------------------------------------------ fig_t1
fig, axes = plt.subplots(1, 2, figsize=(10.0, 4.2))
TH = np.linspace(0, 2 * np.pi, 200)
circle = np.vstack([np.cos(TH), np.sin(TH)])          # unit joint-speed circle
for ax, Jm, name in ((axes[0], J_home, "home 位形"), (axes[1], J_fold, "折叠位形")):
    E = Jm[:, [0, 2]] @ circle                          # FLX / PIP plane
    ax.plot(E[1], E[0], lw=2, color="tab:blue", label="速度椭圆")
    ax.plot(circle[1] * 0, circle[0] * 0, lw=1)
    S = np.linalg.svd(Jm[:, [0, 2]], compute_uv=False)
    ax.set_aspect("equal")
    ax.axhline(0, color="k", lw=0.8)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("ẏ (cm/s per unit ‖θ̇‖)", fontsize=8)
    ax.set_ylabel("ż (cm/s)", fontsize=8)
    ax.set_title("%s　σ1=%.2f σ2=%.2f　κ=%.2f" % (name, S[0], S[1], S[0] / S[1]),
                 fontsize=10)
    ax.legend(fontsize=8, loc="lower right")
axes[0].text(0.02, 0.98, "单位关节速度圆 → 椭圆：\n方向不同，尖端速度差 %.1f 倍"
             % (S_home[0] / S_home[1]), transform=axes[0].transAxes,
             fontsize=8.5, va="top")
fig.suptitle("速度雅可比：J(θ) 把“关节速度的单位圆”映射成“尖端速度椭圆”", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_t1_ellipse.png"))
plt.close(fig)

# ------------------------------------------------------------------ fig_t2
print("sampling the workspace ...", flush=True)
NS = 12000
rng = np.random.default_rng(0)
Q = rng.uniform(RANGES[:, 0], RANGES[:, 1], size=(NS, 4))
pts, kaps, smin = [], [], []
for v in Q:
    Jm, p = jac(qA(v))
    S = np.linalg.svd(Jm, compute_uv=False)
    pts.append(p * 100)
    smin.append(S[-1])
    kaps.append(S[0] / max(S[-1], 1e-6))
pts = np.array(pts)
kaps = np.array(kaps)
smin = np.array(smin)
print("workspace extent  x: %.1f..%.1f  y: %.1f..%.1f  z: %.1f..%.1f cm"
      % (pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max(),
         pts[:, 2].min(), pts[:, 2].max()))
print("kappa range %.1f .. %.1f (median %.1f)" % (kaps.min(), kaps.max(),
                                                  np.median(kaps)))
print("min singular value %.3f .. %.3f cm/rad (median %.2f)"
      % (smin.min(), smin.max(), np.median(smin)))

fig, axes = plt.subplots(1, 2, figsize=(10.4, 4.4))
sc = axes[0].scatter(pts[:, 1], pts[:, 2], c=np.clip(kaps, 1, 20), s=2,
                     cmap="viridis", vmax=12)
plt.colorbar(sc, ax=axes[0], label="条件数 κ(J)")
axes[0].plot(p_home[1] * 100, p_home[2] * 100, "o", ms=9, mfc="none",
             mec="crimson", mew=2)
axes[0].annotate("home", (p_home[1] * 100, p_home[2] * 100),
                 textcoords="offset points", xytext=(6, 6), color="crimson", fontsize=9)
axes[0].set_xlabel("y (cm)")
axes[0].set_ylabel("z (cm)")
axes[0].set_title("侧视图工作空间（Y-Z），颜色 = 条件数", fontsize=10)
axes[0].set_aspect("equal")

sc2 = axes[1].scatter(pts[:, 0], pts[:, 1], c=np.clip(kaps, 1, 20), s=2,
                      cmap="viridis", vmax=12)
plt.colorbar(sc2, ax=axes[1], label="条件数 κ(J)")
axes[1].plot(p_home[0] * 100, p_home[1] * 100, "o", ms=9, mfc="none",
             mec="crimson", mew=2)
axes[1].set_xlabel("x (cm)")
axes[1].set_ylabel("y (cm)")
axes[1].set_title("俯视图工作空间（X-Y）", fontsize=10)
axes[1].set_aspect("equal")
fig.suptitle("单指可达工作空间（随机采样 %d 个位形）：颜色越亮越“各向异性”" % NS,
             fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_t2_workspace.png"))
plt.close(fig)

# ------------------------------------------------------------------ fig_t3
print("running for the torque profile ...", flush=True)


def pd(targets):
    from numpy import clip
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
ts, tq, Mdiag, gmag = [], [], [], []
t = 0.0
for st in range(6000):
    t += m.opt.timestep
    pd(ctl.targets(t, d.qpos, m.opt.timestep))
    mujoco.mj_step(m, d)
    if st % 5 == 0:
        ts.append(t)
        tq.append(np.array([d.actuator_force[LUT[n]] for n in ORDER]))
        if st % 500 == 0:
            Mfull = np.zeros((m.nv, m.nv))
            mujoco.mj_fullM(m, d, Mfull)
            Mdiag.append(np.diag(Mfull)[6:])
            gmag.append(np.abs(d.qfrc_bias[6:]))
ts = np.array(ts)
tq = np.array(tq)
tq_abs = np.abs(tq)
print("peak |tau| = %.2f N·m   RMS = %.2f N·m   limit = 10 N·m"
      % (tq_abs.max(), np.sqrt((tq ** 2).mean())))
print("per-joint peak:", np.round(tq_abs.max(axis=0), 2))
Mdiag = np.array(Mdiag).mean(axis=0)
gmag = np.array(gmag).mean(axis=0)
print("mean |M_diag| of the 16 joints: %.2e .. %.2e kg·m²"
      % (Mdiag.min(), Mdiag.max()))
print("mean |bias torque| (C+G): %.2f .. %.2f N·m" % (gmag.min(), gmag.max()))

fig, axes = plt.subplots(1, 2, figsize=(10.6, 3.8))
axes[0].plot(ts, tq_abs.max(axis=1), lw=1.2, color="tab:red", label="max |τ| over 16 joints")
axes[0].plot(ts, np.sqrt((tq ** 2).mean(axis=1)), lw=1.0, color="tab:blue",
             label="RMS over 16 joints")
axes[0].axhline(10, color="k", ls="--", lw=1.4, label="actuator limit 10 N·m")
axes[0].set_xlabel("time (s)")
axes[0].set_ylabel("torque (N·m)")
axes[0].set_title("实测关节力矩：峰值 %.2f、RMS %.2f N·m（限幅 10）"
                  % (tq_abs.max(), np.sqrt((tq ** 2).mean())), fontsize=10)
axes[0].legend(fontsize=8, loc="upper right")
axes[0].set_ylim(0, 12)

axes[1].bar(np.arange(16), tq_abs.max(axis=0), color="tab:red", alpha=0.85,
            label="peak")
axes[1].bar(np.arange(16), np.sqrt((tq ** 2).mean(axis=0)), color="tab:blue",
            alpha=0.85, label="RMS")
axes[1].set_xticks(np.arange(16))
axes[1].set_xticklabels([n.replace("unit", "") for n in ORDER], rotation=90, fontsize=6)
axes[1].axhline(10, color="k", ls="--", lw=1.2)
axes[1].set_ylabel("torque (N·m)")
axes[1].set_title("逐关节峰值 / RMS", fontsize=10)
axes[1].legend(fontsize=8)
fig.suptitle("电机选型依据：实测负载 vs 10 N·m 限幅（余量 %.1f 倍）"
             % (10 / tq_abs.max()), fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_t3_torque.png"))
plt.close(fig)

# ------------------------------------------------------------------ fig_t4
s = np.linspace(0, 1, 400)
sine = np.sin(2 * np.pi * s)
v_sine = np.gradient(sine, s)
a_sine = np.gradient(v_sine, s)
quin = 10 * s ** 3 - 15 * s ** 4 + 6 * s ** 5
v_quin = np.gradient(quin, s)
a_quin = np.gradient(v_quin, s)
# our actual lift envelope
lift = np.array([_smooth((x - 0.5) / 0.5) if x >= 0.5 else 0 for x in s])
print("\nsine   : peak |v|=%.2f  peak |a|=%.2f  endpoint v=%.2f a=%.2f"
      % (np.abs(v_sine).max(), np.abs(a_sine).max(), abs(v_sine[0]), abs(a_sine[0])))
print("quintic: peak |v|=%.2f  peak |a|=%.2f  endpoint v=%.2f a=%.2f"
      % (np.abs(v_quin).max(), np.abs(a_quin).max(), abs(v_quin[0]), abs(a_quin[0])))

fig, axes = plt.subplots(1, 2, figsize=(10.4, 3.6))
axes[0].plot(s, sine, lw=2, label="sin(2πs)（当前步态）")
axes[0].plot(s, quin, lw=2, label="10s³−15s⁴+6s⁵（五次多项式）")
axes[0].axhline(0, color="k", lw=0.8)
axes[0].set_xlabel("归一化摆动相时间 s")
axes[0].set_ylabel("关节位移")
axes[0].set_title("轨迹形状", fontsize=10)
axes[0].legend(fontsize=8)
axes[1].plot(s, np.abs(v_sine), lw=2, label="|dv/ds| sine")
axes[1].plot(s, np.abs(v_quin), lw=2, label="|dv/ds| quintic")
axes[1].set_xlabel("归一化摆动相时间 s")
axes[1].set_ylabel("|速度|")
axes[1].set_title("五次多项式端点速度为 0，正弦不是", fontsize=10)
axes[1].legend(fontsize=8)
fig.suptitle("摆动相轨迹：当前用正弦，端点仍有速度 → 触地瞬间有冲击", fontsize=11)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig_t4_trajectory.png"))
plt.close(fig)
print("done")
