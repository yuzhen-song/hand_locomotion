"""Record a side-follow mp4 (file name carries model, score and timestamp).

Usage:
  MUJOCO_GL=egl python 07_tools/rec_video.py creep            # record the best model
  MUJOCO_GL=egl python 07_tools/rec_video.py creep --last     # record the latest round
  MUJOCO_GL=egl python 07_tools/rec_video.py low --steps 3000 --seed 0
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths  # noqa: E402

import imageio  # noqa: E402
import mujoco  # noqa: E402
import numpy as np  # noqa: E402
from stable_baselines3 import PPO  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model", nargs="?", default="creep", choices=["creep", "low"])
    ap.add_argument("--last", action="store_true", help="record the latest round instead of the best model")
    ap.add_argument("--steps", type=int, default=3000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--every", type=int, default=8, help="capture one frame every N steps")
    ap.add_argument("--azimuth", type=float, default=0.0, help="0=right side, 90=front")
    a = ap.parse_args()

    paths.ensure_dirs()
    mod = __import__(f"train_quad_{a.model}", fromlist=["QuadWalk"])
    env = mod.QuadWalk()
    kind = "last" if a.last else "best"
    model = PPO.load(paths.ckpt(a.model, kind), env=env, device="cpu")

    obs, _ = env.reset(seed=a.seed)
    renderer = mujoco.Renderer(env.model, height=480, width=640)
    frames, xs = [], []
    for t in range(a.steps):
        act, _ = model.predict(obs, deterministic=True)
        obs, _r, done, _tr, info = env.step(act)
        xs.append(info["x"])
        if t % a.every == 0:
            cam = mujoco.MjvCamera()
            p = np.array(env.data.body("platform_mount").xpos)
            cam.lookat[:] = [float(p[0]), float(p[1]), float(p[2])]
            cam.distance = 0.6
            cam.elevation = -10
            cam.azimuth = a.azimuth
            renderer.update_scene(env.data, camera=cam)
            frames.append(renderer.render().copy())
        if done:
            break

    dx = xs[-1] - xs[0]
    tag = datetime.datetime.now().strftime("%m%d_%H%M")
    out = os.path.join(paths.VIDEO_DIR, f"{a.model}_{kind}_dx{dx:.2f}m_{tag}.mp4")
    imageio.mimsave(out, frames, fps=a.fps)
    print(f"saved {out} steps={len(xs)} dx={dx:.3f}m done={done}")


if __name__ == "__main__":
    main()
