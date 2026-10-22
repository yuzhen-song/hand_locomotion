"""Global paths and configuration. Imported by every script; edit here when moving machines."""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
ENV_DIR = os.path.join(ROOT, "01_env")
TRAIN_DIR = os.path.join(ROOT, "02_train")
MODEL_DIR = os.path.join(ROOT, "03_model")
CKPT_DIR = os.path.join(ROOT, "04_checkpoints")
VIDEO_DIR = os.path.join(ROOT, "05_videos")
PHOTO_DIR = os.path.join(ROOT, "06_photos")
TOOLS_DIR = os.path.join(ROOT, "07_tools")
LOG_DIR = os.path.join(ROOT, "08_logs")

MODEL_XML = os.path.join(MODEL_DIR, "quadruped_sim.xml")


def _cuda_ok():
    try:
        import torch
        return bool(torch.cuda.is_available())
    except Exception:
        return False


def _env_int(key, default):
    try:
        return int(os.environ[key])
    except Exception:
        return default


# "cuda" / "cpu": auto-detected, force with HL_DEVICE=cpu
DEVICE = os.environ.get("HL_DEVICE") or ("cuda" if _cuda_ok() else "cpu")

# Both can be overridden with environment variables for quick runs on a new GPU
N_ENVS = _env_int("HL_N_ENVS", 4)                  # parallel envs; 8 nearly doubles throughput
TRAIN_STEPS_PER_ROUND = _env_int("HL_ROUND_STEPS", 30000)  # training steps per round
EVAL_STEPS = 1000               # evaluation episode length (2 s)
EVAL_SEEDS = (0, 1, 2)          # evaluation seeds
TARGET_DX = 2.0                 # target distance that ends training

for _p in (ROOT, ENV_DIR, TOOLS_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def ckpt(name, kind="last"):
    """kind: last | best"""
    return os.path.join(CKPT_DIR, f"{name}_{kind}")


def ckpt_txt(name):
    return os.path.join(CKPT_DIR, f"{name}_best.txt")


def log(name):
    return os.path.join(LOG_DIR, f"loop_{name}.log")


def ensure_dirs():
    for p in (CKPT_DIR, VIDEO_DIR, LOG_DIR):
        os.makedirs(p, exist_ok=True)
