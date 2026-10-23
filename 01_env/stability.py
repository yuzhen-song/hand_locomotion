"""Stability measurements for the write-up.

For a run it records, at every control tick:
  - the centre of mass (world) and its ground projection
  - which fingertip geoms touch the floor, and where
  - the support polygon (convex hull of the contact points)
  - the static margin: signed distance from the CoM projection to that polygon
  - the ZMP from the measured contact forces
  - the heading

Used by 06_docs/make_stability_figures.py and the numbers quoted in
06_docs/stability_analysis.md.
"""

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "01_env"))
import mujoco  # noqa: E402

from controller import TrotController  # noqa: E402
from gait import PHASE_SETS, CrawlGait, heading_of  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
MODEL = os.path.join(ROOT, "03_model", "quadruped_sim.xml")

LEGS = "ABCD"
TIPB = {"C": "finger_tip", "A": "finger_tip_2", "B": "finger_tip_3", "D": "finger_tip_4"}
FLOOR = 0


def make():
    m = mujoco.MjModel.from_xml_path(MODEL)
    d = mujoco.MjData(m)
    jn = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, i) for i in range(m.njnt)]
    order = [n for n in jn if n and "unit" in n]
    acts = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]
    lut = {n.replace("m_", ""): i for i, n in enumerate(acts)}
    abd = {"C": 0.63, "A": -0.63, "B": 0.63, "D": -0.63}
    q0 = np.array([{"MCP-FLX": -1.10, "MCP-ABD": abd[n.split("-")[0].replace("unit", "")],
                    "PIP": 1.60, "DIP": -0.35}[n.split("-", 1)[1]] for n in order])
    tipbody = {lg: mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, TIPB[lg]) for lg in LEGS}
    return m, d, order, lut, q0, tipbody


def pd(m, d, order, lut, targets):
    u = np.zeros(m.nu)
    q = d.qpos[7:].copy()
    qd = d.qvel[6:].copy()
    for k, n in enumerate(order):
        u[lut[n]] = 40.0 * (targets[k] - q[k]) - 4.0 * qd[k]
    d.ctrl[:] = np.clip(u, -10, 10)


def contacts(m, d):
    """(n,2) positions of floor contacts and (n,) normal forces."""
    pts, fz = [], []
    for i in range(d.ncon):
        c = d.contact[i]
        if c.geom1 != FLOOR and c.geom2 != FLOOR:
            continue
        f = np.zeros(6)
        mujoco.mj_contactForce(m, d, i, f)
        if f[0] <= 1e-6:
            continue
        pts.append(c.pos[:2] * 100)
        fz.append(f[0])
    return np.array(pts).reshape(-1, 2), np.array(fz)


def zmp(m, d):
    """ZMP from the contact wrench (world frame, cm)."""
    num_x = num_y = den = 0.0
    for i in range(d.ncon):
        c = d.contact[i]
        if c.geom1 != FLOOR and c.geom2 != FLOOR:
            continue
        f = np.zeros(6)
        mujoco.mj_contactForce(m, d, i, f)
        R = np.array(c.frame).reshape(3, 3)
        fw = R @ f[:3]          # world force on geom2 (normal along frame x)
        p = c.pos * 100
        num_x += p[0] * fw[2] - p[2] * fw[0]
        num_y += p[1] * fw[2] - p[2] * fw[1]
        den += fw[2]
    if abs(den) < 1e-6:
        return np.array([np.nan, np.nan])
    return np.array([num_x / den, num_y / den])


def _cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


def hull(pts):
    if len(pts) < 3:
        return pts
    pts = pts[np.lexsort((pts[:, 1], pts[:, 0]))]
    def half(P):
        out = []
        for p in P:
            while len(out) >= 2 and _cross2(out[-1] - out[-2], p - out[-2]) <= 0:
                out.pop()
            out.append(p)
        return out
    lower, upper = half(pts), half(pts[::-1])
    return np.array(lower[:-1] + upper[:-1])


def signed_margin(poly, p):
    """Signed distance from p to the polygon boundary, negative outside."""
    if len(poly) < 2:
        return np.nan
    if len(poly) == 2:
        a, b = poly
        ab = b - a
        t = np.clip(np.dot(p - a, ab) / max(np.dot(ab, ab), 1e-9), 0, 1)
        return -float(np.linalg.norm(p - (a + t * ab)))  # a segment has no interior
    inside = True
    best = np.inf
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        ab = b - a
        n = np.array([-ab[1], ab[0]])
        n /= max(np.linalg.norm(n), 1e-9)
        dist = float(np.dot(p - a, n))
        if dist < 0:
            inside = False
        best = min(best, abs(dist))
    return best if inside else -best


def run(gait_name="trot", knee=0.4, bias=-0.10, yaw_gain=-0.20, lat_gain=-2.0,
        lat_tau=4.0, period=None, duty=None, stride=None, steps=12000, every=5,
        open_loop=False):
    m, d, order, lut, q0, tipbody = make()
    kw = dict(period=period or (1.6 if gait_name == "trot" else 2.6),
              duty=duty if duty is not None else (0.5 if gait_name == "trot" else 0.85),
              stride=stride if stride is not None else (0.6 if gait_name == "trot" else 0.35),
              knee=knee, phases=PHASE_SETS[gait_name])
    ctl = None
    gait = CrawlGait(order, q0, **kw)
    if not open_loop:
        ctl = TrotController(order, q0, period=kw["period"], duty=kw["duty"],
                             stride=kw["stride"], knee=knee, phases=gait_name,
                             bias=bias, yaw_gain=yaw_gain, lat_gain=lat_gain,
                             lat_tau=lat_tau)
    mujoco.mj_resetData(m, d)
    d.qpos[2] = 0.14
    d.qpos[7:] = q0
    mujoco.mj_forward(m, d)
    for _ in range(400):
        pd(m, d, order, lut, q0)
        mujoco.mj_step(m, d)
    x0, y0 = float(d.qpos[0]), float(d.qpos[1])
    if ctl is not None:
        ctl.reset(x0, y0)

    rec = dict(t=[], com=[], comz=[], marg=[], zmp=[], ncon=[], poly=[],
               heading=[], speed=[], x=[], y=[])
    t = 0.0
    fell = None
    for st in range(steps):
        t += m.opt.timestep
        if ctl is not None:
            tg = ctl.targets(t, d.qpos, m.opt.timestep)
        else:
            tg = gait.reference(t)
        pd(m, d, order, lut, tg)
        mujoco.mj_step(m, d)
        R = np.array(d.body("platform_mount").xmat).reshape(3, 3)
        if R[2, 0] < 0.7 or d.qpos[2] < 0.05:
            fell = t
            break
        if st % every:
            continue
        com = np.array(d.subtree_com[0]) * 100
        pts, fz = contacts(m, d)
        poly = hull(pts) if len(pts) else np.zeros((0, 2))
        rec["t"].append(t)
        rec["com"].append(com[:2])
        rec["comz"].append(com[2])
        rec["marg"].append(signed_margin(poly, com[:2]) if len(poly) else np.nan)
        rec["zmp"].append(zmp(m, d))
        rec["ncon"].append(len(pts))
        rec["poly"].append(poly)
        rec["heading"].append(math.degrees(heading_of(d.qpos[3:7])))
        rec["speed"].append(float(np.linalg.norm(d.qvel[:2])) * 100)
        rec["x"].append(float(d.qpos[0]) - x0)
        rec["y"].append(float(d.qpos[1]) - y0)
    out = {k: np.array(v, dtype=object) if k == "poly" else np.array(v)
           for k, v in rec.items()}
    out["fell"] = fell
    out["t_end"] = t
    out["dy"] = (float(d.qpos[1]) - y0) if fell is None else np.nan
    return out


def summary(r, name):
    marg = np.array(r["marg"], dtype=float)
    ok = ~np.isnan(marg)
    zx = np.array([z[0] for z in r["zmp"]], dtype=float)
    outside = (marg < 0) & ok
    print(f"{name}: " + ("摔于 %.2fs" % r["fell"] if r["fell"] else
                         "%.1fs 前进 %.1fcm" % (r["t_end"], r["dy"] * 100)))
    print(f"   静态裕度 平均 {np.nanmean(marg):+.2f}cm  最小 {np.nanmin(marg):+.2f}cm  "
          f"最大 {np.nanmax(marg):+.2f}cm")
    print(f"   CoM 在支撑多边形外的时间占比 {outside[ok].mean()*100:.0f}%   "
          f"平均接触点数 {r['ncon'].mean():.1f}（最少 {r['ncon'].min()}）")
    print(f"   ZMP 有效样本 {np.isfinite(zx).mean()*100:.0f}%")
    return dict(mean=np.nanmean(marg), min=np.nanmin(marg),
                frac_out=outside[ok].mean() * 100)


if __name__ == "__main__":
    print("=== 3&1 爬行 ===")
    r = run("crawl", knee=0.0, steps=6000, open_loop=True)
    summary(r, "crawl 3&1 开环")
    print()
    print("=== 2&2 对角（当前调好的配置）===")
    r = run("trot", steps=12000)
    summary(r, "trot 2&2 闭环")
