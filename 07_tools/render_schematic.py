"""Render the classic gait so a human can actually read it.

Two layouts:
  * default: 2D schematic (no OpenGL) - side view with a world ruler, one
    polyline per finger, the swing leg highlighted, plus a top-view inset.
  * --gl: real MuJoCo 3D rendering (needs a working GPU/GL context).

Usage:
  python 07_tools/render_schematic.py --gait crawl --steps 2400
  python 07_tools/render_schematic.py --gait crawl --gl --out 05_videos/gl.mp4
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths  # noqa: E402

import gc  # noqa: E402
import subprocess  # noqa: E402
import tempfile  # noqa: E402

import imageio_ffmpeg  # noqa: E402
import mujoco  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from gait import CrawlGait  # noqa: E402

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
LEG_COLOR = {"A": (255, 86, 86), "B": (255, 170, 40), "C": (80, 190, 255), "D": (120, 240, 120)}
BG = (13, 13, 17)
GROUND = (95, 95, 110)
GRID = (36, 36, 44)
TEXT = (225, 225, 235)
DIM = (110, 110, 125)


def dim(color, k=0.42):
    return tuple(int(c * k) for c in color)


def leg_paths(m, limbs):
    """Proximal-to-distal body chain for each finger."""
    names = [mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b) or "" for b in range(m.nbody)]
    out = {}
    for leg in "ABCD":
        tips = [b for b in range(m.nbody) if limbs.get(b) == leg and "finger_tip" in names[b]]
        if not tips:
            continue
        chain, cur = [], tips[0]
        while cur > 0 and limbs.get(cur) == leg:
            chain.append(cur)
            cur = int(m.body_parentid[cur])
        out[leg] = chain[::-1]
    return out


def body_leg_map(m):
    def leg_of(name):
        for leg in "ABCD":
            if "unit" + leg in name:
                return leg
        return None

    jnt_of_body = {}
    for j in range(m.njnt):
        leg = leg_of(mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, j) or "")
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


def foot_geoms(m, limbs):
    """Collision geoms per finger: their centres are the real contact points."""
    out = {leg: [] for leg in "ABCD"}
    for g in range(m.ngeom):
        name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or ""
        if "tip_collision" not in name:
            continue
        leg = limbs.get(int(m.geom_bodyid[g]))
        if leg:
            out[leg].append(g)
    return out


def draw_schematic(m, d, chain, t, y0, feet=None, scale=1950.0, W=780, H=500):
    """Main panel is a TOP view (X-Y): this hand's four fingers sit in a 2x2
    pattern, so they only separate in X-Y. A side view (Y-Z) goes bottom-right."""
    img = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(img)
    f11 = ImageFont.truetype(FONT, 11)
    f13 = ImageFont.truetype(FONT, 13)
    f16 = ImageFont.truetype(FONT_B, 16)
    f20 = ImageFont.truetype(FONT_B, 20)

    body = np.array(d.body("platform_mount").xpos)
    cx, cy = 470, 250          # pixel position of the body in the top view

    def to_px(y, x):
        return (cx + (y - body[1]) * scale, cy - (x - body[0]) * scale)

    # travel ruler along Y, ground fixed
    base = 420
    dr.line([(40, base), (W - 40, base)], fill=GROUND, width=2)
    for k in range(-60, 61):
        wy = round(body[1] / 0.02) * 0.02 + k * 0.02
        px = to_px(wy, 0.0)[0]
        if not (40 < px < W - 40):
            continue
        major = abs(round(wy * 100) % 10) < 1e-6
        dr.line([(px, base), (px, base - (9 if major else 5))], fill=GROUND if major else GRID, width=1)
        if major:
            dr.text((px - 11, base + 4), f"{wy*100:+.0f}", font=f11, fill=DIM)
    dr.text((44, base + 18), "travel axis +Y (cm, ground-fixed)", font=f11, fill=DIM)

    swing = None
    for leg in "ABCD":
        if GAIT is not None and GAIT.is_swinging(leg, t):
            swing = leg
    for leg, ids in chain.items():
        live = (leg == swing)
        col = LEG_COLOR[leg] if live else dim(LEG_COLOR[leg])
        pts = [to_px(float(d.body(b).xpos[1]), float(d.body(b).xpos[0])) for b in ids]
        if feet and feet.get(leg):
            c = np.mean([d.geom_xpos[g] for g in feet[leg]], axis=0)
            pts.append(to_px(float(c[1]), float(c[0])))
        dr.line(pts, fill=col, width=5 if live else 3, joint="curve")
        for p in pts[:-1]:
            dr.ellipse([p[0] - 3, p[1] - 3, p[0] + 3, p[1] + 3], fill=col)
        x, y = pts[-1]
        dr.ellipse([x - 7, y - 7, x + 7, y + 7], fill=col)
        dr.text((x + 11, y - 9), leg, font=f16, fill=col)

    dr.text((20, 16), "classic crawl gait  (open loop)", font=f20, fill=TEXT)
    dy = (float(body[1]) - y0) * 100
    dr.text((20, 44), f"t = {t:5.2f} s", font=f16, fill=TEXT)
    dr.text((20, 68), f"forward Y = {dy:+6.1f} cm", font=f16,
            fill=(120, 240, 150) if dy > 0 else (255, 140, 140))
    dr.text((20, 92), f"swing leg  = {swing or '-'}", font=f16,
            fill=LEG_COLOR.get(swing, TEXT) if swing else TEXT)
    dr.text((20, 120), "main = TOP view (X-Y), bright = swing", font=f11, fill=DIM)

    # side view inset (Y-Z): shows body height and how little the tips lift
    ox, oy, w2, h2 = W - 250, H - 170, 230, 150
    dr.rectangle([ox, oy, ox + w2, oy + h2], outline=GRID, width=1)
    dr.text((ox + 6, oy + 4), "side view (Y-Z)", font=f11, fill=DIM)
    zc = 0.0
    if feet:
        cs = [np.mean([d.geom_xpos[g] for g in ids], axis=0) for ids in feet.values() if ids]
        if cs:
            zc = float(np.mean([c[2] for c in cs]))
    s2 = 700.0
    g2 = oy + h2 - 26
    dr.line([(ox + 6, g2), (ox + w2 - 6, g2)], fill=GROUND, width=1)
    for leg, ids in chain.items():
        live = (leg == swing)
        col = LEG_COLOR[leg] if live else dim(LEG_COLOR[leg])
        pts = [(ox + w2 / 2 + (float(d.body(b).xpos[1]) - body[1]) * s2,
                g2 - (float(d.body(b).xpos[2]) - zc) * s2) for b in ids]
        if feet and feet.get(leg):
            c = np.mean([d.geom_xpos[g] for g in feet[leg]], axis=0)
            pts.append((ox + w2 / 2 + (float(c[1]) - body[1]) * s2, g2 - (float(c[2]) - zc) * s2))
        dr.line(pts, fill=col, width=2, joint="curve")

    return img


GAIT = None


def main():
    global GAIT
    ap = argparse.ArgumentParser()
    ap.add_argument("--gait", default="crawl", choices=["crawl", "hold"])
    ap.add_argument("--steps", type=int, default=2400)
    ap.add_argument("--every", type=int, default=16)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default=None)
    ap.add_argument("--gl", action="store_true", help="MuJoCo 3D rendering instead of the schematic")
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
    GAIT = CrawlGait(order, q0, period=1.2, duty=0.75, stride=0.45, knee=0.22)

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

    limbs = body_leg_map(m)
    chain = leg_paths(m, limbs)
    feet = foot_geoms(m, limbs)
    gl = mujoco.Renderer(m, height=480, width=640) if a.gl else None
    out = a.out or os.path.join(paths.VIDEO_DIR, f"gait_{a.gait}{'_gl' if a.gl else '_schematic'}.mp4")
    y0 = float(d.qpos[1])
    t, fell = 0.0, None
    tmp = tempfile.mkdtemp(prefix="gaitframes_")
    nframe = [0]
    is_gif = out.lower().endswith(".gif")
    frames = []

    def emit(frame):
        if is_gif:
            # 8-bit palette keeps an 80-frame animation under 30 MB of RAM
            frames.append(frame.convert("P", palette=Image.ADAPTIVE, colors=96))
        else:
            frame.save(os.path.join(tmp, f"f{nframe[0]:05d}.png"))
        nframe[0] += 1
        if nframe[0] % 10 == 0:
            gc.collect()

    try:
        for step in range(a.steps):
            t += m.opt.timestep
            pd(GAIT.reference(t) if a.gait == "crawl" else q0)
            mujoco.mj_step(m, d)
            R = np.array(d.body("platform_mount").xmat).reshape(3, 3)
            if R[2, 0] < 0.7 or d.qpos[2] < 0.05:
                fell = step
            if step % a.every == 0:
                if gl is None:
                    emit(draw_schematic(m, d, chain, t, y0, feet))
                else:
                    cam = mujoco.MjvCamera()
                    p = np.array(d.body("platform_mount").xpos)
                    cam.lookat[:] = [float(p[0]), float(p[1]), float(p[2])]
                    cam.distance = 0.6
                    cam.elevation = -10
                    cam.azimuth = 0
                    gl.update_scene(d, camera=cam)
                    emit(Image.fromarray(gl.render()))
            if fell is not None:
                for _ in range(a.fps):
                    if gl is None:
                        emit(draw_schematic(m, d, chain, t, y0, feet))
                break
    finally:
        # free the MuJoCo model before shelling out to ffmpeg: on a 2 GB
        # container the encoder would otherwise push the process over the limit
        gl = None
        del m, d
        gc.collect()
        if is_gif:
            frames[0].save(out, save_all=True, append_images=frames[1:],
                           duration=max(20, 1000 // a.fps), loop=0, optimize=True)
            print(f"saved {out} frames={len(frames)}")
            return
        ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
        subprocess.run([ffmpeg, "-y", "-loglevel", "error", "-framerate", str(a.fps),
                        "-i", os.path.join(tmp, "f%05d.png"), "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", out], check=True)
        for f in os.listdir(tmp):
            os.remove(os.path.join(tmp, f))
        os.rmdir(tmp)
    print(f"saved {out} steps={a.steps if fell is None else fell} dx={float(d.qpos[1])-y0:+.3f}m fell={fell}")


if __name__ == "__main__":
    main()
