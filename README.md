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

## 6. Classic gait + residual RL (work in progress)

`01_env/gait.py` holds an open-loop crawl gait generator: one leg swings at a
time (duty 0.75, order A -> D -> B -> C), and each leg's hip sweeps front to
back during stance and back to front during swing.

Open-loop test result (no policy, pure PD tracking of the reference):

| Variant | Net displacement in 3.6 s | Falls |
|---|---|---|
| crawl, stride 0.45 rad, 1.2 s cycle | **-0.209 m** (backward) | none |
| crawl, slower cycle (2.0 s) | -0.091 m | none |
| crawl, faster cycle (0.7 s) | -0.374 m | none |
| all four legs in phase (shuffle) | +0.027 m | none |
| crawl with 8x tip friction | -0.034 m | none |

Conclusion: the reference is dynamically stable (tilt < 0.01, never falls) but
produces **no net thrust**. Measured cause: the fingertip has almost no
vertical authority - the full joint range lifts it by only ~4 mm - so the swing
leg cannot clear the ground, and the symmetric sweep cancels out over a cycle.
Raising tip friction removes the backward drift but does not create forward
motion.

Therefore the classic gait cannot act as the controller for this hand; it can
only serve as a **rhythm/phase prior** for residual RL (phase in the
observation, residual torque or residual angle on top of the reference).
`07_tools/render_schematic.py` renders the gait without OpenGL, for machines where
the GPU is unavailable. It draws:

* **side view** (Y horizontal, Z vertical), one polyline per finger through its
  four bodies plus the fingertip collision proxy, ending on the contact line
* the **swing leg in full colour**, stance legs dimmed, so the A -> D -> B -> C
  order is visible at a glance
* a **ground-fixed ruler** in cm that scrolls as the body moves, which makes the
  (absent) forward motion obvious
* a HUD with time, forward displacement, body height and the active swing leg
* a **top-view inset** with the four fingertips in world X-Y

Output: `05_videos/classic_gait_schematic.gif` (GIF, so it renders inline on
GitHub). Add `--gl` on a machine with a GPU for real MuJoCo 3D rendering.

### Residual RL environment

`01_env/train_quad_residual.py` wraps the crawl reference:

```
q_target = q_ref(phase) + residual * 0.35 rad
torque   = PD(q_target)          # same safety filter and force limits as creep
obs      = qpos + qvel + sin/cos(phase of each leg)   -> 53 numbers
reward   = creep reward minus the hand-made crawl clock
           minus 0.5 * |q - q_ref|  minus 0.2 * |residual|
```

The point: the reference supplies the rhythm and the leg ordering, the policy
only has to learn the asymmetric loading that produces thrust (which the hand
cannot do open loop, see above).

Train it with the existing loop, just pass the name:

```bash
python 02_train/train_until_walk_creep.py residual     # -> 04_checkpoints/residual_*.zip
python 07_tools/rollout_measure.py residual --kind best
```

### Fingertip friction sweep (crawl gait, 4.8 s open loop)

| tip friction | net displacement | falls |
|---|---|---|
| 2.0 (model default) | -0.246 m | no |
| 4.0 | **-0.065 m** | no |
| 6.0 | -0.002 m | yes (step 1442) |
| 10.0 | -0.058 m | no |
| 16.0 | -0.109 m | no |

Raising friction to 4.0 removes most of the backward slip; 6.0 is the stability
limit. It still does not create forward thrust - the sweep stays symmetric -
but the hand no longer slides backwards.

Multi-view recording (side follow, 3/4 front, top, feet close-up):

```bash
MUJOCO_GL=osmesa python 07_tools/render_schematic.py --gl --views \
    --gait crawl --friction 4.0 --steps 1600 --every 40 \
    --out 05_videos/classic_gait_4views.mp4
```

Output: `05_videos/classic_gait_4views.{mp4,gif}`.

### It walks (open loop) with two changes: friction 5 and a slow high-duty gait

Earlier the crawl gait produced no net motion (fingertips slip, the symmetric
sweep cancels out). Two changes fix it:

1. fingertip sliding friction **2.0 -> 5.0**
2. a **slow, high-duty** cycle: period **2.6 s**, duty **0.85**, stride **0.35 rad**, knee flex 0

With that, the pure open-loop reference walks **forward and stays up**:

| time | forward Y | body height |
|---|---|---|
| 3 s | +0.020 m | 0.116 m |
| 6 s | +0.037 m | 0.124 m |
| 12 s | +0.091 m | 0.123 m |
| 18 s | +0.139 m | 0.124 m |
| 24 s | +0.183 m | 0.125 m |
| 30 s | **+0.222 m** | 0.122 m |

Roughly 0.75 cm/s, steady, no falls. Slow, but it is real open-loop walking -
the hip sweep now grips during stance instead of sliding.

Search notes (2400 steps = 4.8 s per trial, fingertip friction in brackets):

- friction 2.0, any crawl setting: all <= 0 (best -0.09 m)
- friction 4.0: first positive results (best +0.028 m at T=1.6, duty=0.85)
- friction 5.0: 30 of 72 settings positive, best **+0.041 m** at T=2.6, duty=0.85, stride=0.35
- friction 6.0+ or duty=1.0: no better

Record it:

```bash
MUJOCO_GL=osmesa python 07_tools/render_schematic.py --gl --views --gait crawl \
    --friction 5.0 --period 2.6 --duty 0.85 --stride 0.35 --knee 0.0 \
    --steps 5000 --every 80 --out 05_videos/classic_walk_4views.mp4
```

Output: `05_videos/classic_walk_4views.{mp4,gif}`.

### Defaults changed (friction 5 is now baked into the model)

`03_model/quadruped_sim.xml` now uses fingertip friction **5.0** (was 2.0), and
the walking configuration **period 2.6 s / duty 0.85 / stride 0.35 / knee 0** is
the default of `gait.CrawlGait`. Every consumer follows automatically:

- the residual env (`train_quad_residual.py`) uses it as its reference
- `render_schematic.py` uses it for the multi-view recording
- `rollout_measure.py` / `rec_video.py` see the new physics

Sanity check after the change: the pure open-loop reference covers **+0.07 m in
12 s** with no policy, and the residual env's mean reward is already **positive
(+0.075)** with random actions, i.e. the reference itself is earning progress.

Note: checkpoints in `04_checkpoints/` were trained under friction 2.0, so their
measured distance shifts slightly with the new model. Retrain from scratch (or
fine-tune) for comparable numbers.

### Status: residual RL (400k steps) is worse than the open-loop reference

Measured over 10 s, deterministic rollout:

| controller | forward Y | sideways X | final yaw | max |yaw| |
|---|---|---|---|---|
| open-loop reference | **+0.065 m** | +0.003 m | +34 deg | 180 deg |
| residual PPO, 400k steps | -0.024 m | -0.005 m | +83 deg | 140 deg |

The policy did not beat the reference: the reward is still dominated by
accumulated penalties (lateral drift and yaw are integrated over a 5000-step
episode), so PPO finds degenerate behaviours instead of speed. The reference
stays the best controller so far.

Heading is the open problem: the 2x2 finger layout produces a systematic yaw
moment, and the hand turns up to 180 deg on its own. A classical differential
stride controller (`gait.yaw_scale`) only reaches ~100 deg and costs forward
speed, and a common MCP-ABD offset has no measurable lateral effect, so neither
fixes it.

Long recording of the reference gait (30 s, four cameras):

`05_videos/classic_walk_long_4views.{mp4,gif}`

### Why is it so slow? (measured breakdown)

Mass 1.14 kg. Hip (MCP-FLX) usable range [-1.57, +0.23], home -1.10; PIP
[-0.49, +1.89], home +1.60. Tip sensitivity 5.3 cm/rad on the hip.

Kinematic ceiling of the current gait:

| quantity | value |
|---|---|
| hip sweep per cycle | 0.70 rad |
| fingertip travel per cycle | 3.71 cm |
| stance duration | 2.21 s (2.6 s x 0.85) |
| **ceiling, zero slip** | **1.68 cm/s** |
| **measured** | **0.57 cm/s** (34%) |

Speed resolved by gait phase (averaged over several cycles):

| phase | mean v | which leg swings |
|---|---|---|
| 0.50-0.55 | **+9.2 / +7.8 cm/s** | none (all four down) |
| 0.10-0.20 | +1.7 .. +2.8 | C |
| 0.30-0.40 | **-2.7 / -2.1** | B |
| 0.90-0.95 | **-3.8 / -7.8** | A |

The body surges forward then is pulled back every time a leg swings. The swing
(recovery) stroke runs at ~9.5 cm/s, 5.6x the stance push speed, so its braking
dominates. Root cause: **all four fingertips are in floor contact at every
phase** (12 contacts in all 20 phase buckets, never zero) - the swing leg never
leaves the ground, because joint motion lifts a tip by only ~5 mm.

Tested and rejected:

| hypothesis | experiment | result |
|---|---|---|
| contact rolls/slips | condim 4 -> 6, rolling friction 0.005-0.1 | 0.47-0.57, no change |
| rear legs drag | rear stride x0 / x0.3 | 0.57 -> 0.33 (slower) |
| rear legs not loaded | rear PIP -0.1 .. -0.3 | 0.57 -> 0.37 (slower) |
| servos too soft | PD tracking error | 0.016 rad, fine |
| round 4.3 cm ball proxy | replaced each tip with a flat 14 mm pad | all settings go backward |

Conclusion: ~0.6 cm/s is structural for this hand, not a tuning problem. The
5 mm of foot lift is the hard limit; without clearance the recovery stroke
always brakes the body. Going faster needs more joint range or longer fingers,
not a different spring or friction value.

### Which axis, and which gait? (measured)

Fingertip authority, full joint range, world frame:

| joint | range | tip X | tip Y | tip Z | X per rad |
|---|---|---|---|---|---|
| MCP-FLX | 1.80 rad | 0.00 cm | **8.6-10.7 cm** | 0.55 cm | - |
| MCP-ABD | 2.92 rad | **2.77 cm** | 2.57 cm | 1.31 cm | 0.95 cm/rad |
| PIP | 2.38 rad | 2.54 cm | 5.43 cm | 2.99 cm | - |
| DIP | 2.31 rad | 0 | 0 | 0 | - |

MCP-ABD has the widest range but the smallest tip travel: it rotates the finger
about an axis nearly parallel to the finger, so the tip barely translates. X is
therefore the *worse* direction (2.77 cm vs 8.6 cm usable stroke).

Sweeping MCP-ABD (walking in X), 16 configs over four phase patterns, all walk
essentially nowhere (|v| < 0.6 cm/s, mostly negative) and the 2&2 side pattern
falls over twice. Walking in Y is the only viable direction.

Gait comparison while sweeping MCP-FLX (Y), 13 s per trial:

| gait | period | stride | knee | Y speed | X drift | max tilt |
|---|---|---|---|---|---|---|
| 3&1 crawl ADBC | 1.6 | 0.35 | 0.0 | +0.46 cm/s | +0.6 cm | 0.015 |
| 3&1 crawl ADBC | 2.6 | 0.6 | 0.0 | +0.44 | +1.7 | 0.046 |
| **2&2 diagonal AD/BC** | 2.6 | 0.6 | 0.2 | **+0.60** | +2.8 | 0.033 |
| **2&2 diagonal AD/BC** | 1.6 | 0.6 | 0.2 | **+1.19** | +9.3 | 0.032 |
| 2&2 side AC/BD | any | any | any | all negative | | falls |
| 2&2 front/back | any | any | any | all negative | | |

The 2&2 diagonal trot is 1.3-2.6x faster than the crawl, and it only works with
a knee flex (knee=0 gives ~0): with two legs swinging at once the recovery lasts
twice as long, so retracting the swing leg matters. The fast 1.19 cm/s setting
pays for it with 9 cm of sideways drift.

### Straightening the trot: a constant stride bias removes the sideways drift

The 2&2 diagonal trot moves +0.45 m forward but +0.43 m sideways in 40 s (it
crawls at ~43 deg off the target). Feedback on X position or velocity through
differential stride does nothing (X drift stays 0.6-1.0 cm/s for every gain).

A *constant* stride bias does work. Scale the +X legs (A, C) by (1-bias) and the
-X legs (B, D) by (1+bias):

| bias | forward | sideways | heading |
|---|---|---|---|
| 0.00 | +1.13 cm/s | +0.43 cm/s | +43 deg |
| -0.205 | +0.83 | +0.17 | +11.8 deg |
| **-0.21** | **+0.94** | **+0.06** | **+3.6 deg** |
| -0.215 | +1.09 | -0.16 | -8.3 deg |

At bias ~-0.212 the hand walks essentially straight at ~1.0 cm/s, i.e. straight
at about 90% of the drifting speed. Recording:

`05_videos/trot_straight_40s.{mp4,gif}` (bias -0.212, zoom 1.25)

### Yaw feedback on the trot: +85% speed and relatively straighter

The constant bias cancels the mean drift, but the body still spins (yaw swings
+-100 deg), so the path wobbles: the first 5 s veer +42 deg and later the
instantaneous heading swings +-25 deg, though the cumulative error stays within
+-7 deg and |X| stays under 6.6 cm over 40 s.

A yaw P controller on the stride differential (scaling the +X/-X pairs in
opposite directions) does have authority:

| yaw gain | forward | sideways | lateral/distance |
|---|---|---|---|
| 0.0 | +1.00 cm/s | -0.02 | 16.5% |
| 0.3 | +1.59 | +0.19 | - |
| **0.5** | **+1.85 cm/s** | +0.19 | **11%** |
| 0.6 | falls | | |

Damping the spin frees energy that was going into rotation: **+85% speed** and a
lower sideways-to-forward ratio. Recording (bias -0.212, yaw gain 0.5):

`05_videos/trot_fast_straight_40s.{mp4,gif}`

### Did RL beat the hand-tuned controller? No (third attempt)

The residual env now sits on the fast straight trot (bias -0.212, yaw gain 0.5),
with a retuned reward (stagnation off, target 5 cm/s, sigma 0.03, smoothness
0.4, lateral/yaw penalties) so that zero residual already earns +0.197/step.

600k PPO steps on the RTX 4090:

| controller | mean reward / step | 10 s forward | 10 s sideways | survives |
|---|---|---|---|---|
| zero residual (reference) | **+0.197** | +0.162 m | +0.026 m | yes |
| residual RL, 600k steps | +0.154 (peak 0.154) | +0.024 m | +0.094 m | **falls at 0.5 s** |

The policy never climbed above the "do nothing" baseline and, in rollout, walks
into a sideways fall within half a second (same on three seeds).

Three RL attempts (400k, 400k, 600k steps) have all failed to beat the
deterministic reference on this hand. The reference plus a scalar yaw P gain
(1.85 cm/s, 11% sideways) is still the best controller. The blocker is actuator
authority - four fingertips that never leave the ground, 5 mm of lift and
2.77 cm of lateral stroke leave little for a learned controller to exploit.

### Correction: the foot can lift ~2 cm, the 5 mm figure was measured with knee=0

The earlier claim that "5 mm of foot lift is the hard limit" was wrong. 5.2 mm
is what the tip moves passively when the gait commands no lift (knee=0).

Measured tip height against PIP angle (kinematics only):

| PIP | -0.49 | 0.0 | 0.80 | 1.20 | 1.60 (home) | 1.89 (limit) |
|---|---|---|---|---|---|---|
| tip z | 35.50 cm | 33.83 | 31.92 | 31.68 | 31.98 | 32.51 |

Flexing PIP past the flat spot raises the tip, and the tip travels ~3 cm over
the joint range. Widening the PIP limit from 1.89 to 2.50 rad changes nothing in
the gait (1.41 -> 1.41 cm/s), so the joint stop is not the binding constraint.

What actually matters is the gait's `knee` (swing flex) parameter:

| knee | forward (no bias/yaw) | foot clearance |
|---|---|---|
| 0.2 | +1.41 cm/s | 1.79 cm |
| 0.4 | +2.88 | 2.07 |
| 0.6 | **+3.20 cm/s** | 2.23 |

So the structure is fine and there is a 2.3x speed headroom in the parameters.
The trade-off is stability: with the straight-tuned bias (-0.212) and yaw gain
0.5, knee 0.4 veers (sideways/forward 89%), knee 0.6 falls, and increasing the
bias to compensate falls within 0.8 s. Speed and straightness cannot currently
be had at the same time; the best stable point stays at knee 0.2
(1.82 cm/s, 6% sideways, max 5.8 cm lateral in 25 s).

That coupling - three gains and strong nonlinear interactions - is exactly the
kind of tuning a learned controller should beat a human at, which is the
remaining argument for RL here.

### knee x bias x yaw grid + closed loop: 3.04 cm/s, 6x the first gait

36-point grid (25 s each), scored as speed x straightness:

| knee | bias | yaw | forward | sideways | max lateral | score |
|---|---|---|---|---|---|---|
| **0.4** | **-0.16** | **0.3** | **+3.11 cm/s** | +0.28 | 8.6 cm | **2.83** |
| 0.4 | -0.21 | 0.3 | +2.99 | +0.23 | 7.0 | 2.76 |
| 0.3 | -0.16 | 0.3 | +2.91 | +0.27 | 10.3 | 2.64 |
| 0.3 | -0.21 | 0.7 | +2.50 | -0.06 | **4.2** | 2.44 |

Closed loop on the lateral position (bias_eff = bias + lat_gain*x) adds a little
on top of the open-loop bias: at knee 0.4 / bias -0.16 / yaw 0.3, lat_gain -2.0
gives 3.18 cm/s at 7% sideways (vs 3.11 at 9%); lat_gain -3 falls.

Final setting, 40 s: **+1.214 m forward, 3.04 cm/s, 15 cm lateral** (13%).
Recording: `05_videos/trot_fastest_40s.{mp4,gif}`

Progress of the forward speed across the session:

| gait | forward speed |
|---|---|
| crawl, first working version | 0.49 cm/s |
| crawl, tuned | 0.57 |
| 2&2 trot + bias + yaw | 1.82 |
| **trot + grid + closed loop** | **3.04 cm/s (6.2x)** |

### Slow outer loop (low-pass on the lateral error)

Acting on the raw lateral position makes the two loops fight. Low-passing the
outer error with time constant tau:

| outer loop | forward | sideways | max lateral |
|---|---|---|---|
| none | 3.08 cm/s | 9% | 11.9 cm |
| fast (tau 0.8 s), lat_gain -2 | 3.03 | 7% | 10.1 |
| **slow (tau 4 s), lat_gain -2** | **3.11** | **6%** | **9.4** |
| slow (tau 2 s), lat_gain -3 | 2.93 | 4% | 6.9 |
| lat_gain -4 | falls | | |

Integral-only outer loop is worse (2.60 cm/s at 11%) or falls. Best compromise:
tau 4 s with lat_gain -2 -> 3.11 cm/s at 6%. If straightness matters more,
tau 2 s with lat_gain -3 gives 2.93 cm/s at 4%.

Recording: `05_videos/trot_best_40s.{mp4,gif}`

### The controller is now a class: `01_env/controller.py`

The three-level cascade is packaged as `TrotController`:

```python
from controller import TrotController
ctl = TrotController(order, q0)          # defaults = the 3.11 cm/s setting
ctl.reset(x0, y0)                        # once, after the body settles
while ...:
    q_target = ctl.targets(t, d.qpos, dt)  # feed to a PD loop
    ...
```

`targets()` is the only interface: it reads the base qpos, updates the yaw and
lateral loops internally (the lateral error is low-passed with a 4 s constant),
and returns the joint targets.  It reproduces the tuned run exactly: 40 s ->
1.243 m forward, 3.11 cm/s, 6% sideways, 9.4 cm max lateral.  The renderer now
drives this class instead of repeating the loop inline, so the same object can
later carry an online-tuned (RL) set of gains.
