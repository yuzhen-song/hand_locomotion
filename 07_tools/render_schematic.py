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
import math
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

from controller import TrotController  # noqa: E402
from gait import PHASE_SETS, SIDE, CrawlGait, yaw_of  # noqa: E402

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
    ap.add_argument("--gait", default="crawl", choices=["crawl", "trot", "pace", "bound", "hold"])
    ap.add_argument("--steps", type=int, default=2400)
    ap.add_argument("--every", type=int, default=16)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--out", default=None)
    ap.add_argument("--gl", action="store_true", help="MuJoCo 3D rendering instead of the schematic")
    ap.add_argument("--views", action="store_true", help="2x2 multi-camera grid (needs --gl)")
    ap.add_argument("--period", type=float, default=None, help="gait cycle in seconds")
    ap.add_argument("--duty", type=float, default=None, help="stance fraction per leg")
    ap.add_argument("--stride", type=float, default=None, help="hip sweep amplitude in rad")
    ap.add_argument("--knee", type=float, default=None, help="swing knee flex in rad")
    ap.add_argument("--zoom", type=float, default=1.0, help="camera distance multiplier")
    ap.add_argument("--yaw_gain", type=float, default=0.0,
                    help="P gain on yaw; differential stride correction that damps the body spin")
    ap.add_argument("--lat_gain", type=float, default=0.0,
                    help="closed loop on lateral position: bias_eff = bias + lat_gain*x")
    ap.add_argument("--lat_tau", type=float, default=0.0,
                    help="low-pass time constant (s) on the lateral error; slow outer loop")
    ap.add_argument("--bias", type=float, default=0.0,
                    help="differential stride bias: +X legs x(1-bias), -X legs x(1+bias); use to cancel sideways drift")
    ap.add_argument("--friction", type=float, default=None,
                    help="override the fingertip sliding friction (model default 2.0)")
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
    DEFAULTS = {"trot": dict(period=1.6, duty=0.5, stride=0.6, knee=0.2),
                "pace": dict(period=2.6, duty=0.5, stride=0.6, knee=0.2),
                "bound": dict(period=2.6, duty=0.5, stride=0.6, knee=0.2)}
    kw = dict(DEFAULTS.get(a.gait, dict(period=2.6, duty=0.85, stride=0.35, knee=0.0)))
    kw["phases"] = PHASE_SETS.get(a.gait, PHASE_SETS["crawl"])
    for key in ("period", "duty", "stride", "knee"):
        if getattr(a, key) is not None:
            kw[key] = getattr(a, key)
    print(f"gait {a.gait}: {kw}", flush=True)
    GAIT = CrawlGait(order, q0, **kw)
    CTL = None
    if a.bias or a.yaw_gain or a.lat_gain:
        CTL = TrotController(order, q0, period=kw["period"], duty=kw["duty"],
                             stride=kw["stride"], knee=kw["knee"],
                             phases=a.gait if a.gait in PHASE_SETS else "crawl",
                             bias=a.bias, yaw_gain=a.yaw_gain,
                             lat_gain=a.lat_gain, lat_tau=a.lat_tau)

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
    if a.friction is not None:
        for ids in feet.values():
            for g in ids:
                m.geom_friction[g, 0] = a.friction
                m.geom_friction[g, 1] = a.friction
        print(f"friction -> {a.friction}", flush=True)
    gl = mujoco.Renderer(m, height=200, width=264) if a.gl else None
    if gl is not None:
        # software rendering: shadows dominate the cost, they are not worth it here
        gl.scene.flags[mujoco.mjtRndFlag.mjRND_SHADOW] = False
        gl.scene.flags[mujoco.mjtRndFlag.mjRND_REFLECTION] = False

    def single_view():
        cam = mujoco.MjvCamera()
        p = np.array(d.body("platform_mount").xpos)
        cam.lookat[:] = [float(p[0]), float(p[1]), float(p[2])]
        cam.distance = 0.6
        cam.elevation = -10
        cam.azimuth = 0
        gl.update_scene(d, camera=cam)
        return Image.fromarray(gl.render())

    def add_box(scene, pos, size, rgba):
        if scene.ngeom >= scene.maxgeom:
            return
        g = scene.geoms[scene.ngeom]
        mujoco.mjv_initGeom(g, mujoco.mjtGeom.mjGEOM_BOX, np.asarray(size, dtype=float),
                            np.asarray(pos, dtype=float), np.eye(3).flatten(),
                            np.asarray(rgba, dtype=np.float32))
        scene.ngeom += 1

    def add_ruler(scene, y0):
        """World-fixed ticks on the floor, so translation is unmistakable."""
        for k in range(-4, 61):
            yy = y0 + k * 0.02
            major = (k % 5 == 0)
            add_box(scene, [0.0, yy, 0.0008],
                    [0.09 if major else 0.05, 0.0012 if major else 0.0007, 0.0008],
                    [0.2, 0.85, 0.35, 1] if major else [0.35, 0.4, 0.45, 1])

    def grab_views():
        """Fixed world cameras: the body visibly crosses the frame."""
        y0w = y0
        z = a.zoom
        specs = ((0, -12, 0.60 * z, "FIXED SIDE (world frame)"),
                 (135, -22, 0.62 * z, "FIXED 3/4"),
                 (0, -80, 0.50 * z, "FIXED TOP"),
                 (40, -14, 0.30, "FEET CLOSE-UP (follow)"))
        tile = Image.new("RGB", (528, 400), BG)
        dr = ImageDraw.Draw(tile)
        fnt = ImageFont.truetype(FONT, 12)
        cur = np.array(d.body("platform_mount").xpos)
        for i, (az, el, dist, label) in enumerate(specs):
            cam = mujoco.MjvCamera()
            if i == 3:
                cam.lookat[:] = [float(cur[0]), float(cur[1]), float(cur[2]) - 0.09]
            else:
                cam.lookat[:] = [0.0, y0w + 0.20 + 0.30 * (z - 1.0), 0.05]
            cam.distance = dist
            cam.elevation = el
            cam.azimuth = az
            gl.update_scene(d, camera=cam)
            add_ruler(gl.scene, y0w)
            im = Image.fromarray(gl.render())
            x, y = (i % 2) * 264, (i // 2) * 200
            tile.paste(im, (x, y))
            dr.rectangle([x, y, x + 262, y + 198], outline=(70, 70, 85))
            dr.rectangle([x, y, x + len(label) * 7 + 10, y + 19], fill=(0, 0, 0))
            dr.text((x + 5, y + 4), label, font=fnt, fill=TEXT)
        dy = (float(d.body("platform_mount").xpos[1]) - y0w) * 100
        dr.rectangle([4, 372, 300, 396], fill=(0, 0, 0))
        dr.text((8, 375), f"t={t:5.2f}s   forward Y={dy:+6.1f} cm   (green tick = {5} cm)",
                font=fnt, fill=TEXT)
        return tile

    out = a.out or os.path.join(paths.VIDEO_DIR, f"gait_{a.gait}{'_gl' if a.gl else '_schematic'}.mp4")
    y0 = float(d.qpos[1])
    x0 = float(d.qpos[0])
    t, fell = 0.0, None
    if CTL is not None:
        CTL.reset(float(d.qpos[0]), float(d.qpos[1]))
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
            if a.gait == "hold":
                pd(q0)
            elif CTL is not None:
                pd(CTL.targets(t, d.qpos, m.opt.timestep))
            else:
                pd(GAIT.reference(t))
            mujoco.mj_step(m, d)
            R = np.array(d.body("platform_mount").xmat).reshape(3, 3)
            if R[2, 0] < 0.7 or d.qpos[2] < 0.05:
                fell = step
            if step % a.every == 0:
                if gl is None:
                    emit(draw_schematic(m, d, chain, t, y0, feet))
                else:
                    emit(grab_views() if a.views else single_view())
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
    print(f"saved {out} frames={nframe[0]} fell={fell}")


if __name__ == "__main__":
    main()
