"""Evaluate a checkpoint over EVAL_SEEDS seeds and print the mean forward distance."""
import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths  # noqa: E402

import numpy as np  # noqa: E402
from stable_baselines3 import PPO  # noqa: E402


def build_env(name):
    mod = __import__(f"train_quad_{name}", fromlist=["QuadWalk"])
    return mod, mod.QuadWalk()


def measure(name, kind="last", steps=None, seeds=None, device="cpu", verbose=True):
    _mod, env = build_env(name)
    ck = paths.ckpt(name, kind)
    model = PPO.load(ck, env=env, device=device)
    steps = steps or paths.EVAL_STEPS
    seeds = seeds or paths.EVAL_SEEDS
    dxs = []
    for seed in seeds:
        obs, _ = env.reset(seed=seed)
        xs = []
        done = False
        for _ in range(steps):
            a, _ = model.predict(obs, deterministic=True)
            obs, _r, done, _tr, info = env.step(a)
            xs.append(info["x"])
            if done:
                break
        dxs.append(xs[-1] - xs[0])
    mean = float(np.mean(dxs))
    if verbose:
        print(f"dxs={[round(float(v), 3) for v in dxs]} dx={mean:.3f}m")
    return mean, dxs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model", nargs="?", default="creep", choices=["creep", "low"])
    ap.add_argument("--kind", default="last", choices=["last", "best"])
    ap.add_argument("--steps", type=int, default=None)
    ap.add_argument("--seeds", type=int, nargs="*", default=None)
    ap.add_argument("--device", default="cpu")
    a = ap.parse_args()
    measure(a.model, a.kind, a.steps, tuple(a.seeds) if a.seeds else None, a.device)


if __name__ == "__main__":
    main()
