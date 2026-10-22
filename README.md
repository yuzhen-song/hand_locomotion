# hand_locomotion — Locomotion RL for a 16-DoF Robotic Hand

A 16-DoF mechanical hand (4 fingers x 4 joints) is used as a quadruped. PPO learns to make it
walk. Travel direction is fixed to **+Y** — the hand's geometry only allows sideways
(crab-like) locomotion, it cannot advance along X.

Current best: **0.679 m** per 2-second evaluation (3-seed average); a 6-second rollout covers
**1.10 m** without falling.

## 1. Layout

```
hand_locomotion/
├── paths.py                      Global config: all paths + hyper-parameters
├── requirements.txt              Pinned dependencies
├── README.md                     This file
├── start_doctor.bat              Windows launcher: deployment self-check
├── start_train_creep.bat         Windows launcher: start training
├── start_record.bat              Windows launcher: record a video
│
├── 01_env/                       [Environments and rewards]
│   ├── train_quad_creep.py       Main env: crawl gait (legs cycle A->D->B->C at 0.35 Hz)
│   └── train_quad_low.py         Control env: same model/reward, crawl clock disabled
│
├── 02_train/                     [Training loops]
│   ├── train_until_walk_creep.py 30k steps -> evaluate (3 seeds) -> keep best -> stop at 2 m
│   └── train_until_walk_low.py   Same loop for the control run
│
├── 03_model/                     [Physics model]
│   ├── quadruped_sim.xml         Training model (actuator force limit opened to +/-10)
│   ├── quadruped.xml             Original model (+/-4 limit, reference only)
│   └── my-robot/assets/          Mesh directory (109 files; 40 referenced by the XML)
│
├── 04_checkpoints/               [Weights]
│   ├── creep_last.zip            Latest completed round (overwritten each round)
│   ├── creep_best.zip + .txt     Best score so far (monotonic)
│   ├── low_last.zip / low_best.zip + .txt   Same for the control run
│   └── archive/                  Historical checkpoints (reference only, do not resume)
│
├── 05_videos/                    [Videos] mp4, named <model>_<kind>_dx<score>_<date>.mp4
├── 06_photos/                    [Photos] standing poses, q0 pose, empty scene
│
├── 07_tools/                     [Tools]
│   ├── doctor.py                 Deployment self-check: 9 checks, reports what is missing
│   ├── rollout_measure.py        Evaluate: python 07_tools/rollout_measure.py creep [--kind best]
│   └── rec_video.py              Record: python 07_tools/rec_video.py creep [--last] [--steps 3000]
│
└── 08_logs/                      [Logs] loop_creep.log / loop_low.log (per-round dx history)
```

## 2. Deployment

### 2.1 Linux server

```bash
cd hand_locomotion
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export MUJOCO_GL=egl            # headless GPU rendering; use osmesa if there is no GPU

python 07_tools/doctor.py       # self-check: must pass before training

nohup python 02_train/train_until_walk_creep.py > 08_logs/loop_creep.log 2>&1 &
```

All paths in `paths.py` are derived from `__file__`, so the folder can be moved anywhere
without editing code.

Tunable through environment variables (no file edits needed):

| Variable | Default | Meaning |
|---|---|---|
| `HL_DEVICE` | auto (`cuda`/`cpu`) | Forces the training device; falls back to CPU if no GPU |
| `HL_N_ENVS` | 4 | Parallel environments; 8-16 on an A100/4090 roughly doubles throughput |
| `HL_ROUND_STEPS` | 30000 | Training steps per round; use `2048` for a quick pipeline test |

### 2.2 Windows laptop (RTX 4090 Laptop, Ada)

```powershell
cd D:\hand_locomotion
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install mujoco==3.15.0 stable-baselines3==2.9.0 gymnasium==1.4.0 numpy==2.5.4 imageio==2.38.1 imageio-ffmpeg==0.6.0
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121

python 07_tools\doctor.py        # or double-click start_doctor.bat

$env:HL_N_ENVS = "6"             # 4-6 is plenty; MuJoCo is CPU-bound
python 02_train\train_until_walk_creep.py     # or double-click start_train_creep.bat
```

Differences from Linux:

- **Rendering backend**: on Windows use `MUJOCO_GL=glfw` or leave it unset. `egl` does not
  exist on Windows and will fail. The recorder opens an OpenGL window — leave it open.
- **torch build**: the laptop 4090 is Ada (sm_89), so the standard `cu121` wheel is correct.
  Blackwell cards (RTX 5090) need `torch>=2.7.1 --index-url .../whl/cu128`.
- Keep the folder on a local drive, short path, no spaces, and out of OneDrive.
- Plug in the charger and use the high-performance power profile; battery mode cuts GPU clock.

### 2.3 What to upload

| Required | Size | Notes |
|---|---|---|
| `paths.py`, `requirements.txt`, `README.md` | small | config and docs |
| `01_env/`, `02_train/`, `07_tools/` | small | all code |
| `03_model/` | 24 MB | physics model + meshes, cannot be skipped |
| `04_checkpoints/*.zip`, `*.txt` | 9 MB | weights and scores; without them training starts from zero |

| Optional | Size | Notes |
|---|---|---|
| `05_videos/` | 60 MB | history, not needed for training |
| `04_checkpoints/archive/` | 7 MB | old checkpoints, do not resume from them |
| `08_logs/` | 0.9 MB | old logs, kept for reference |

Minimal package is about **35 MB**.

## 3. Common commands

```bash
# train (background)
nohup python 02_train/train_until_walk_creep.py > 08_logs/loop_creep.log 2>&1 &
nohup python 02_train/train_until_walk_low.py   > 08_logs/loop_low.log   2>&1 &

# progress
grep -a -E "round|dx=|new best|SUCCESS" 08_logs/loop_creep.log | tail -n 5
cat 04_checkpoints/creep_best.txt

# record (best or latest round)
MUJOCO_GL=egl python 07_tools/rec_video.py creep
MUJOCO_GL=egl python 07_tools/rec_video.py creep --last --steps 3000

# stop
pkill -9 -f train_until_walk; pkill -9 -f "train_quad_"
```

## 4. Key conventions (read before changing code)

1. **Travel direction is +Y.** `info["x"]` actually reports `qpos[1]` (the Y coordinate).
2. **Front legs are A and B** (largest Y). Front-leg torque is scaled x1.5 (cap +/-6);
   the rear legs are not scaled.
3. **Vertical axis**: `R = platform_mount.xmat`, the up direction is column 0, so the vertical
   component is `R[2, 0]` — *not* `R[0, 2]`. (Getting this wrong makes every episode end
   immediately with "fall".)
4. **Knee hard constraint**: when a PIP joint drops below 0.6 and the commanded torque still
   pushes it down, that torque is zeroed (torque-level safety filter).
5. **Stance q0**: deep squat plus lateral splay (C:+0.63 / A:-0.63 / B:+0.63 / D:-0.63),
   which widens the support polygon from 0.116 m to 0.137 m.
6. **Measurement conventions**: evaluation is 1000 steps (2 s) averaged over 3 seeds, while the
   recorder runs 3000 steps (6 s) once. The two numbers are not comparable.
7. **Reward terms (creep)**: speed tracking (0.12 m/s, weight 3) + progress x40 + alive 0.02
   - stagnation 0.8 - tilt 12 - non-tip contact 0.5 - pose deviation 1.5 - knee fold 3
   - action smoothness 1.5 + swing 0.3 + crawl clock 6 - tip pointing up 4 - action cost 0.01.
   Falling costs -20.

## 5. Current status (2026-10-16)

| Run | Best dx (2 s, 3-seed avg) | Video (6 s, single run) | Notes |
|---|---|---|---|
| creep (crawl gait) | 0.679 m | 1.10 m without falling | Main run; previously stopped mid-walk, fixed with a stagnation penalty |
| low (free gait) | 0.645 m | 0.91 m | Shaky, falls occasionally; smoothness penalty raised to 1.5, not yet verified |

Known issues:

- Front knees are very stiff (PIP of A/B barely moves), so the gait looks like rear legs
  stepping while the front legs act as struts.
- The creep run degraded once because the reward was exploitable (a stagnation penalty of 2.5
  was too harsh, lowered to 0.8).
- Older checkpoints were trained with a slightly different knee threshold, so their measured
  score can differ by a few percent.
