"""Training loop: train N steps -> evaluate -> save a new best -> stop when the target is hit.

Usage:
  python 02_train/train_until_walk_low.py      # run in background: nohup ... > 08_logs/loop_low.log 2>&1 &
  python 02_train/train_until_walk_low.py
"""
import os
import shutil
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths  # noqa: E402
from rollout_measure import measure  # noqa: E402

NAME = sys.argv[1] if len(sys.argv) > 1 else "low"


def main():
    paths.ensure_dirs()
    rnd = 0
    while True:
        rnd += 1
        print(f"=== {NAME} round {rnd}: train {paths.TRAIN_STEPS_PER_ROUND} ===", flush=True)
        import subprocess
        rc = subprocess.run(
            [sys.executable, os.path.join(paths.ENV_DIR, f"train_quad_{NAME}.py"),
             str(paths.TRAIN_STEPS_PER_ROUND), "--resume"],
            cwd=paths.ROOT).returncode
        if rc != 0:
            print(f"training exited with code {rc}, retrying in 10s", flush=True)
            import time
            time.sleep(10)
        try:
            dx, _raw = measure(NAME, "last")
        except Exception:
            traceback.print_exc()
            dx = None
        print(f"=== {NAME} round {rnd}: dx={dx}m ===", flush=True)

        bestf = paths.ckpt_txt(NAME)
        try:
            best = float(open(bestf).read().strip())
        except Exception:
            best = -1e9
        if dx is not None and dx > best:
            open(bestf, "w").write(str(dx))
            shutil.copy(paths.ckpt(NAME, "last") + ".zip", paths.ckpt(NAME, "best") + ".zip")
            print(f"*** new best {dx}m saved ***", flush=True)
        if dx is not None and dx >= paths.TARGET_DX:
            print(f"{NAME.upper()} SUCCESS", flush=True)
            break


if __name__ == "__main__":
    main()
