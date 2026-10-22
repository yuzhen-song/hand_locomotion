"""Schematic renderer: draws the mechanism skeleton without OpenGL.

Useful on machines where the GPU is gone and mujoco.Renderer cannot get a GL
context. Two panels: side view (Y-Z) and top view (X-Y), body follows the
platform so the gait stays in frame.

Usage:
  python 07_tools/render_schematic.py --gait crawl --steps 2400 --out 05_videos/x.mp4
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths  # noqa: E402

import imageio.v2 as imageio  # noqa: E402
import mujoco  # noqa: E402
from gait import CrawlGait  # noqa: E402

LEG_COLORS = {"A": (255, 90, 90), "B": (255, 170, 40), "C": (70, 190, 255), "D": (120, 255, 120)}
GROUND_COLOR = (70, 70, 80)
GRID_COLOR = (45, 45, 55)
BODY_COLOR = (230, 230, 240)


def skeleton(m):
    """(child_body_id, parent_body_id) pairs, skipping the world."""
    pairs = []
    for b in range(1, m.nbody):
        p = int(m.body_parentid[b])
        pairs.append((b, p))
    return pairs


def leg_of(name):
    for leg in ("A", "B", "C", "D"):
        if "unit" + leg in name:
            return leg
    return None


def body_leg_map(m):
    """Map every body to the leg that drives it (bodies carry no 'unit' prefix)."""
    jnt_of_body = {}
    for j in range(m.njnt):
        jn = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j) or ""
        leg = leg_of(jn)
        if leg:
            jnt_of_body[int(m.jnt_bodyid[j])] = leg
    limbs = {}
    for b in range(1, m.nbody):
        cur, leg = b, None
        while cur > 0:
            if cur in jnt_of_body:
                leg = jnt_of_body[cur]
                break
            cur = int(m.body_parentid[cur])
        limbs[b] = leg
    return limbs


def draw_line(img, x0, y0, x1, y1, color, w=1):
    h, wd = img.shape[:2]
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    xs = np.linspace(x0, x1, n).astype(int)
    ys = np.linspace(y0, y1, n).astype(int)
    for dx in range(-w, w + 1):
        for dy in range(-w, w + 1):
            xx = np.clip(xs + dx, 0, wd - 1)
            yy = np.clip(ys + dy, 0, h - 1)
            img[yy, xx] = color


def draw_dot(img, cx, cy, color, r=2):
    h, wd = img.shape[:2]
    for dx in range(-r, r + 1):
        for dy in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                x, y = int(cx + dx), int(cy + dy)
                if 0 <= x < wd and 0 <= y < h:
                    img[y, x] = color


def render_frame(m, d, pairs, scale, H, W, limbs):
    """Side view on the left, top view on the right."""
    img = np.zeros((H, W, 3), dtype=np.uint8)
    img[:, :] = (18, 18, 22)
    half = W // 2
    body = np.array(d.body("platform_mount").xpos)

    for panel, (ax_h, ax_v) in enumerate(((1, 2), (1, 0))):
        ox = panel * half
        gy = int(H * 0.72)
        # ground line and world grid
        draw_line(img, ox, gy, ox + half - 1, gy, GROUND_COLOR, 1)
        for k in range(-30, 31):
            yw = round(body[1] * 10) / 10 + k * 0.05
            px = int(ox + half / 2 + (yw - body[1]) * scale)
            if ox < px < ox + half:
                draw_line(img, px, gy, px, H - 1, GRID_COLOR, 0)
        cx = ox + half / 2
        for child, parent in pairs:
            p0 = np.array(d.body(parent).xpos) if parent > 0 else np.zeros(3)
            p1 = np.array(d.body(child).xpos)
            leg = limbs.get(child) or limbs.get(parent)
            color = LEG_COLORS.get(leg, BODY_COLOR)
            x0 = cx + (p0[ax_h] - body[ax_h]) * scale
            y0 = gy - p0[ax_v] * scale
            x1 = cx + (p1[ax_h] - body[ax_h]) * scale
            y1 = gy - p1[ax_v] * scale
            draw_line(img, x0, y0, x1, y1, color, 1)
            draw_dot(img, x1, y1, color, 2)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gait", default="crawl", choices=["crawl", "hold"])
    ap.add_argument("--steps", type=int, default=2400)
    ap.add_argument("--every", type=int, default=16)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--scale", type=float, default=700.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--gl", action="store_true", help="use MuJoCo OpenGL rendering instead of the skeleton")
    a = ap.parse_args()

    paths.ensure_dirs()
    m = mujoco.MjModel.from_xml_path(paths.MODEL_XML)
    d = mujoco.MjData(m)
    jnts = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, i) for i in range(m.njnt)]
    order = [n for n in jnts if n and "unit" in n]
    acts = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(m.nu)]
    lut = {n.replace("m_", ""): i for i, n in enumerate(acts)}
    abd = {"C": 0.63, "A": -0.63, "B": 0.63, "D": -0.63}
    q0 = np.array([{"MCP-FLX": -1.10, "MCP-ABD": abd[n.split("-")[0].replace("unit", "")],
                    "PIP": 1.60, "DIP": -0.35}[n.split("-", 1)[1]] for n in order])
    gait = CrawlGait(order, q0, period=1.2, duty=0.75, stride=0.45, knee=0.22)

    def pd(target):
        u = np.zeros(m.nu)
        q = d.qpos[7:].copy()
        qd = d.qvel[6:].copy()
        for k, jn in enumerate(order):
            u[lut[jn]] = 40.0 * (target[k] - q[k]) - 4.0 * qd[k]
        d.ctrl[:] = np.clip(u, -10, 10)

    mujoco.mj_resetData(m, d)
    d.qpos[2] = 0.14
    d.qpos[7:] = q0
    mujoco.mj_forward(m, d)
    for _ in range(200):
        pd(q0)
        mujoco.mj_step(m, d)

    pairs = skeleton(m)
    limbs = body_leg_map(m)
    gl_renderer = None
    if a.gl:
        gl_renderer = mujoco.Renderer(m, height=480, width=640)
    H, W = 300, 520
    out = a.out or os.path.join(paths.VIDEO_DIR, "gait_crawl_schematic.mp4")
    y0 = float(d.qpos[1])
    t = 0.0
    writer = imageio.get_writer(out, fps=a.fps, macro_block_size=None)
    fell = None
    try:
        for step in range(a.steps):
            t += m.opt.timestep
            target = gait.reference(t) if a.gait == "crawl" else q0
            pd(target)
            mujoco.mj_step(m, d)
            R = np.array(d.body("platform_mount").xmat).reshape(3, 3)
            if R[2, 0] < 0.7 or d.qpos[2] < 0.05:
                fell = step
            if step % a.every == 0:
                if gl_renderer is None:
                    writer.append_data(render_frame(m, d, pairs, a.scale, H, W, limbs))
                else:
                    cam = mujoco.MjvCamera()
                    p = np.array(d.body("platform_mount").xpos)
                    cam.lookat[:] = [float(p[0]), float(p[1]), float(p[2])]
                    cam.distance = 0.6
                    cam.elevation = -10
                    cam.azimuth = 0
                    gl_renderer.update_scene(d, camera=cam)
                    writer.append_data(gl_renderer.render())
            if fell is not None:
                for _ in range(a.fps):
                    writer.append_data(render_frame(m, d, pairs, a.scale, H, W, limbs))
                break
    finally:
        writer.close()
    dx = float(d.qpos[1]) - y0
    print(f"saved {out} steps={a.steps if fell is None else fell} dx={dx:+.3f}m fell={fell}")


if __name__ == "__main__":
    main()
