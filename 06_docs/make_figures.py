"""Generate every figure used in 06_docs/dynamics_analysis.md."""

import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "01_env"))
import mujoco  # noqa: E402

from controller import TrotController  # noqa: E402
from gait import PHASE_SETS, SIDE, CrawlGait, heading_of  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
FIG = os.path.join(ROOT, "06_docs", "figs")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({"figure.dpi": 130, "font.size": 9,
                     "axes.grid": True, "grid.alpha": 0.3})

m = mujoco.MjModel.from_xml_path(os.path.join(ROOT, "03_model", "quadruped_sim.xml"))
d = mujoco.MjData(m)
JN = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, i) for i in range(m.njnt)]
ORDER = [n for n in JN if n and "unit" in n]
ACTS = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]
LUT = {n.replace("m_", ""): i for i, n in enumerate(ACTS)}
ABD0 = {"C": 0.63, "A": -0.63, "B": 0.63, "D": -0.63}
Q0 = np.array([{"MCP-FLX": -1.10, "MCP-ABD": ABD0[n.split("-")[0].replace("unit", "")],
                "PIP": 1.60, "DIP": -0.35}[n.split("-", 1)[1]] for n in ORDER])
JIDX = {n: k for k, n in enumerate(ORDER)}
TIPB = {"C": "finger_tip", "A": "finger_tip_2", "B": "finger_tip_3", "D": "finger_tip_4"}
LEGS = "ABCD"


def settle(n=400):
    mujoco.mj_resetData(m, d)
    d.qpos[2] = 0.14
    d.qpos[7:] = Q0
    mujoco.mj_forward(m, d)
    for _ in range(n):
        pd(Q0)
        mujoco.mj_step(m, d)


def pd(targets):
    u = np.zeros(m.nu)
    q = d.qpos[7:].copy()
    qd = d.qvel[6:].copy()
    for k, n in enumerate(ORDER):
        u[LUT[n]] = 40.0 * (targets[k] - q[k]) - 4.0 * qd[k]
    d.ctrl[:] = np.clip(u, -10, 10)


def run(controller=None, gait=None, steps=20000, log_tips=False):
    settle()
    x0, y0 = float(d.qpos[0]), float(d.qpos[1])
    if controller is not None:
        controller.reset(x0, y0)
    t = 0.0
    xs, ys, yaws, tipsh, scales = [], [], [], [], []
    for st in range(steps):
        t += m.opt.timestep
        if controller is not None:
            tg = controller.targets(t, d.qpos, m.opt.timestep)
            sc = controller.last_scales
        else:
            tg = gait.reference(t)
            sc = None
        pd(tg)
        mujoco.mj_step(m, d)
        xs.append(float(d.qpos[0]) - x0)
        ys.append(float(d.qpos[1]) - y0)
        yaws.append(math.degrees(heading_of(d.qpos[3:7])))
        if log_tips:
            tipsh.append([float(d.body(b).xpos[2]) * 100 for b in TIPB.values()])
        R = np.array(d.body("platform_mount").xmat).reshape(3, 3)
        if R[2, 0] < 0.7 or d.qpos[2] < 0.05:
            return None
    return dict(t=t, x=np.array(xs), y=np.array(ys), yaw=np.array(yaws),
                tips=np.array(tipsh) if log_tips else None)


# ---------------------------------------------------------------- fig 1: layout
settle()
base = np.array(d.body("platform_mount").xpos)
fig, ax = plt.subplots(figsize=(5.2, 3.6))
tips = {lg: np.array(d.body(TIPB[lg]).xpos) for lg in LEGS}
for lg in LEGS:
    ax.plot([base[0] * 100, tips[lg][0] * 100], [base[1] * 100, tips[lg][1] * 100],
            "-o", color="0.6", ms=3, lw=1)
    ax.annotate(f"{lg}\n({tips[lg][0]*100:+.1f}, {tips[lg][1]*100:+.1f})",
                (tips[lg][0] * 100, tips[lg][1] * 100), textcoords="offset points",
                xytext=(4, 4), fontsize=8)
ax.plot(base[0] * 100, base[1] * 100, "s", color="crimson", ms=8, label="body origin")
ax.arrow(0, -9.5, 0, 3, head_width=0.7, head_length=0.6, color="tab:blue", lw=1.5)
ax.text(0.4, -6.0, "+Y  travel", color="tab:blue", fontsize=9)
ax.arrow(0, -9.5, 3, 0, head_width=0.7, head_length=0.6, color="tab:green", lw=1.5)
ax.text(3.4, -9.9, "+X", color="tab:green", fontsize=9)
ax.set_aspect("equal")
ax.set_xlabel("X (cm)")
ax.set_ylabel("Y (cm)")
ax.set_title("Contact layout, seen from above\nstance span 12.7 cm (X) x 18.2 cm (Y)")
ax.legend(loc="upper left", fontsize=8)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig1_layout.png"))
plt.close(fig)

# ------------------------------------------------------- fig 2: joint authority
axes_lbl = ("X", "Y", "Z")
rows = []
for n in ORDER:
    j = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, n)
    lo, hi = m.jnt_range[j]
    leg = n.split("-")[0].replace("unit", "")
    kv = JIDX[n]
    q = Q0.copy()
    q[kv] = lo
    d.qpos[7:] = q
    mujoco.mj_forward(m, d)
    p_lo = np.array(d.body(TIPB[leg]).xpos)
    q[kv] = hi
    d.qpos[7:] = q
    mujoco.mj_forward(m, d)
    p_hi = np.array(d.body(TIPB[leg]).xpos)
    rows.append((n.replace("unitC-", ""), (p_hi - p_lo) * 100, hi - lo))
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
names = [r[0] for r in rows if r[0].startswith("MCP") or r[0].startswith("PIP") or r[0].startswith("DIP")]
uniq = ["MCP-FLX", "MCP-ABD", "PIP", "DIP"]
dv = {u: [r for r in rows if r[0] == u][0][1] for u in uniq}
rng = {u: [r for r in rows if r[0] == u][0][2] for u in uniq}
xx = np.arange(len(uniq))
w = 0.26
for i, ax_i in enumerate(range(3)):
    axes[0].bar(xx + (ax_i - 1) * w, [dv[u][ax_i] for u in uniq], w, label=axes_lbl[ax_i])
axes[0].set_xticks(xx)
axes[0].set_xticklabels([f"{u}\n({rng[u]:.2f} rad)" for u in uniq], fontsize=8)
axes[0].axhline(0, color="k", lw=0.8)
axes[0].set_ylabel("fingertip travel over full joint range (cm)")
axes[0].set_title("Which joint moves the tip where (leg C)")
axes[0].legend(fontsize=8)
eff = {u: abs(dv[u][1]) / rng[u] for u in uniq}
axes[1].bar(list(eff), list(eff.values()), color=["tab:blue", "tab:orange", "tab:green", "0.6"])
axes[1].set_ylabel("cm of tip travel per rad")
axes[1].set_title("Authority per radian: Y is 6x cheaper than X")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig2_authority.png"))
plt.close(fig)

# ------------------------------------------------- fig 3: tip height vs PIP
pips = np.linspace(-0.49, 2.60, 80)
zs = []
for p in pips:
    q = Q0.copy()
    q[JIDX["unitC-PIP"]] = p
    d.qpos[7:] = q
    mujoco.mj_forward(m, d)
    zs.append(float(d.body(TIPB["C"]).xpos[2]) * 100)
fig, ax = plt.subplots(figsize=(5.6, 3.2))
ax.plot(pips, zs, lw=2, label="tip z (kinematics)")
ax.axvspan(1.60, 1.89, color="tab:green", alpha=0.18, label="usable fold at home pose")
ax.axvline(1.89, color="tab:red", ls="--", lw=1.2, label="PIP limit 1.89 rad")
ax.axvline(1.60, color="k", ls=":", lw=1, label="home 1.60 rad")
ax.plot([1.60], [np.interp(1.60, pips, zs)], "o", color="k")
ax.set_xlabel("PIP angle (rad)")
ax.set_ylabel("tip height above the mount (cm)")
ax.set_title("Folding the finger is what lifts the toe")
ax.legend(fontsize=7.5, loc="upper left")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig3_tipheight.png"))
plt.close(fig)

# ----------------------------------------------------- fig 4: trot phase plan
ph = PHASE_SETS["trot"]
period = 1.6
duty = 0.5
fig, ax = plt.subplots(figsize=(6.6, 2.6))
for i, lg in enumerate("ABCD"):
    off = ph[lg]
    for k in range(-1, 3):
        s0 = (k * period) + off * period
        st_end = s0 + duty * period
        sw_end = s0 + period
        if st_end > 0 and s0 < 2 * period:
            ax.barh(i, st_end - s0, left=s0, height=0.55, color="tab:blue", alpha=0.75)
            ax.barh(i, sw_end - st_end, left=st_end, height=0.55, color="tab:orange", alpha=0.75)
ax.set_yticks(range(4))
ax.set_yticklabels([f"leg {l}" for l in "ABCD"])
ax.set_xlim(0, 2.4)
ax.set_xlabel("time (s)")
ax.set_title("2&2 diagonal trot: blue = stance, orange = swing (period 1.6 s, duty 0.5)")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig4_phases.png"))
plt.close(fig)

# ------------------------------------- fig 5: tip path in one cycle + scales
ctl = TrotController(ORDER, Q0)
settle()
x0, y0 = float(d.qpos[0]), float(d.qpos[1])
ctl.reset(x0, y0)
paths = {lg: [] for lg in LEGS}
tt, sc_trace = [], []
t = 0.0
for st in range(2400):
    t += m.opt.timestep
    tg = ctl.targets(t, d.qpos, m.opt.timestep)
    sc = ctl.last_scales
    pd(tg)
    mujoco.mj_step(m, d)
    tt.append(t)
    sc_trace.append([sc[l] for l in "ABCD"])
    for lg in LEGS:
        paths[lg].append(np.array(d.body(TIPB[lg]).xpos) - np.array(d.body("platform_mount").xpos))
sc_trace = np.array(sc_trace)
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
for lg, c in zip(LEGS, ("tab:blue", "tab:orange", "tab:green", "tab:red")):
    P = np.array(paths[lg])[600:1500]
    axes[0].plot(P[:, 1] * 100, P[:, 0] * 100, lw=1.4, color=c, label=f"leg {lg}")
axes[0].set_xlabel("Y relative to body (cm)")
axes[0].set_ylabel("X relative to body (cm)")
axes[0].set_title("Tip path in the body frame (step + return)")
axes[0].legend(fontsize=7.5)
axes[0].set_aspect("equal", adjustable="datalim")
for i, lg in enumerate("ABCD"):
    axes[1].plot(tt, sc_trace[:, i], lw=1.2, label=f"leg {lg}")
axes[1].set_xlabel("time (s)")
axes[1].set_ylabel("stride scale")
axes[1].set_title("Differential stride: bias + yaw + lateral correction")
axes[1].legend(fontsize=7.5, ncol=2)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig5_tippath.png"))
plt.close(fig)

# ------------------------------------------- fig 6/7: parameter sweeps
def speed_of(knee, bias, yg, lat_gain=-2.0, lat_tau=4.0, steps=12500):
    c = TrotController(ORDER, Q0, knee=knee, bias=bias, yaw_gain=yg,
                       lat_gain=lat_gain, lat_tau=lat_tau)
    r = run(controller=c, steps=steps, log_tips=True)
    if r is None:
        return None
    dy, dx = r["y"][-1], r["x"][-1]
    span = (r["tips"].max(axis=1) - r["tips"].min(axis=1)).mean()
    return dy / r["t"] * 100, abs(dx) / max(abs(dy), 1e-6) * 100, span


knees = [0.0, 0.2, 0.3, 0.4, 0.5, 0.6]
kres = [speed_of(k, -0.16, 0.3) for k in knees]
fig, ax1 = plt.subplots(figsize=(5.8, 3.2))
v = [r[0] if r else np.nan for r in kres]
cl = [r[2] if r else np.nan for r in kres]
ax1.plot(knees, v, "o-", color="tab:blue", label="forward speed (cm/s)")
ax1.set_xlabel("knee (swing flex, rad)")
ax1.set_ylabel("forward speed (cm/s)", color="tab:blue")
ax2 = ax1.twinx()
ax2.plot(knees, cl, "s--", color="tab:orange", label="foot clearance (cm)")
ax2.set_ylabel("mean foot clearance (cm)", color="tab:orange")
ax2.grid(False)
ax1.set_title("Faster with more lift, until it falls (gap = fall)")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig6_knee.png"))
plt.close(fig)

biases = [-0.40, -0.31, -0.26, -0.21, -0.16, -0.11, -0.06]
bres = [speed_of(0.4, b, 0.3) for b in biases]
fig, ax = plt.subplots(figsize=(5.8, 3.2))
bb = [b for b, r in zip(biases, bres) if r]
hh = [math.degrees(math.atan(r[1] / 100.0)) * (1 if r[0] > 0 else -1) for b, r in zip(biases, bres) if r]
ax.plot(bb, hh, "o-", color="tab:purple")
ax.axhline(0, color="k", lw=0.8)
ax.set_xlabel("stride bias (negative = +X legs push harder)")
ax.set_ylabel("sideways / forward  (deg off course)")
ax.set_title("Bias steers the course: one scalar controls the heading")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig7_bias.png"))
plt.close(fig)

# --------------------------------------------------- fig 8: control diagram
fig, ax = plt.subplots(figsize=(9.4, 3.6))
ax.set_xlim(0, 12)
ax.set_ylim(0, 5)
ax.axis("off")


def box(x, y, w, h, txt, fc):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                                fc=fc, ec="0.3", lw=1.2))
    ax.text(x + w / 2, y + h / 2, txt, ha="center", va="center", fontsize=8.5)


def arrow(x1, y1, x2, y2, color="0.25", txt=None, dy=0.18):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=12, color=color, lw=1.3))
    if txt:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + dy, txt, fontsize=7.5,
                ha="center", color=color)


box(0.2, 2.6, 1.9, 0.9, "gait clock\nphase phi(t)", "#e8f0fe")
box(2.4, 2.6, 1.9, 0.9, "open-loop\nreference q_ref", "#e8f0fe")
box(4.6, 2.6, 1.0, 0.9, "sum", "#f3f3f3")
box(6.0, 2.6, 1.6, 0.9, "PD loop\n(tau = 25 ms)", "#fff4e5")
box(8.0, 2.6, 1.6, 0.9, "hand + contacts\n(plant)", "#fde8e8")
box(4.0, 4.0, 2.4, 0.8, "feedforward bias", "#e6f4ea")
box(0.2, 0.3, 2.4, 0.85, "inner: yaw P\n(gain 0.3)", "#e6f4ea")
box(3.2, 0.3, 2.6, 0.85, "outer: lateral P\n(gain -2, 4 s LPF)", "#e6f4ea")
ax.text(5.0, 4.85, "differential stride scales s_leg", fontsize=8, style="italic")
arrow(2.1, 3.05, 2.4, 3.05)
arrow(4.3, 3.05, 4.6, 3.05)
arrow(5.6, 3.05, 6.0, 3.05)
arrow(7.6, 3.05, 8.0, 3.05)
ax.text(7.8, 2.85, "q_target", fontsize=7.5, ha="center")
arrow(9.6, 2.6, 9.6, 1.9, color="tab:red")
ax.text(9.7, 2.0, "qpos, qvel", fontsize=7.5, color="tab:red")
arrow(9.6, 1.9, 2.6, 1.9, color="tab:red")
arrow(2.6, 1.9, 2.6, 1.15, color="tab:red")
ax.text(6.2, 1.75, "feedback", fontsize=7.5, color="tab:red")
arrow(9.6, 1.9, 1.4, 1.9, color="tab:red")
arrow(1.4, 1.9, 1.4, 1.15, color="tab:red")
arrow(2.6, 0.72, 5.2, 0.72, color="tab:green")
ax.text(3.9, 0.5, "x error -> bias", fontsize=7.5, color="tab:green")
arrow(2.6, 0.72, 5.2, 0.72, color="tab:green")
arrow(1.4, 1.15, 1.4, 1.55, color="tab:purple")
ax.text(1.55, 1.35, "yaw", fontsize=7.5, color="tab:purple")
arrow(1.55, 1.55, 4.6, 3.9, color="tab:purple")
ax.text(3.2, 2.15, "scales multiply the stride", fontsize=7.5, color="0.35")
fig.suptitle("Three-level cascade: feedforward bias + yaw P (fast) + lateral P (slow, low-passed)",
             fontsize=9, y=0.98)
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig8_control.png"))
plt.close(fig)

# ------------------------------------------------ fig 9/10: the finished run
ctl_best = TrotController(ORDER, Q0)
best = run(controller=ctl_best, steps=20000, log_tips=True)
fig, axes = plt.subplots(1, 2, figsize=(9.2, 3.4))
axes[0].plot(best["y"] * 100, best["x"] * 100, lw=1.4, color="tab:blue")
axes[0].axhline(0, color="k", lw=0.8)
axes[0].set_xlabel("forward Y (cm)")
axes[0].set_ylabel("sideways X (cm)")
axes[0].set_title(f"40 s path: {best['y'][-1]*100:.0f} cm forward, "
                  f"{abs(best['x'][-1])*100:.0f} cm sideways")
axes[0].set_aspect("equal", adjustable="datalim")
axes[1].plot(best["t"] * np.ones_like(best["yaw"]), best["yaw"], lw=1.0, color="tab:red", alpha=0.8)
axes[1].set_xlabel("time (s)")
axes[1].set_ylabel("body yaw (deg)")
axes[1].set_title("Heading: the palm only swings +-10 deg (it is not spinning)")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig9_run.png"))
plt.close(fig)

# ------------------------------------------------- fig 10: progression
labels = ["crawl\nfirst", "crawl\ntuned", "trot+bias\n+yaw", "grid+closed\nloop"]
vals = [0.49, 0.57, 1.82, 3.11]
fig, ax = plt.subplots(figsize=(5.6, 3.0))
bars = ax.bar(labels, vals, color=["0.7", "0.55", "tab:blue", "tab:green"])
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 0.08, f"{v:.2f}", ha="center", fontsize=9)
ax.set_ylabel("forward speed (cm/s)")
ax.set_title("6.3x, all of it from gait and controller tuning")
fig.tight_layout()
fig.savefig(os.path.join(FIG, "fig10_progress.png"))
plt.close(fig)

print("figures written to", FIG)
for f in sorted(os.listdir(FIG)):
    print("  ", f)
print(f"final run: {best['y'][-1]*100:.1f} cm forward, "
      f"{best['y'][-1]/best['t']*100:.2f} cm/s, "
      f"yaw std {np.std(best['yaw']):.0f} deg")
