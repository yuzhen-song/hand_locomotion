"""Residual RL on top of the classic crawl gait.

The reference comes from gait.CrawlGait (open loop, phase driven). The policy
only outputs a bounded joint-space correction:

    q_target = q_ref(phase) + residual * RESIDUAL_SCALE     (RESIDUAL_SCALE rad)
    torque   = PD(q_target)  with the same safety filter and force limits

Why this instead of free RL: the open-loop reference keeps the rhythm and the
leg ordering, so the policy only has to learn the asymmetric loading that
creates thrust - the part this hand cannot do open loop (the fingertip can only
lift ~4 mm, so the reference alone produces no net motion).

Extra observation: sin/cos of each leg's gait phase (8 numbers).
Extra reward terms: tracking the reference, and a penalty on residual size.
"""
import os
import sys

import numpy as np
from gymnasium import spaces

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths  # noqa: E402

import mujoco  # noqa: E402

from gait import CrawlGait  # noqa: E402
import train_quad_creep as _base  # noqa: E402
from train_quad_creep import (  # noqa: E402
    FRONT,
    KNEE_FLOOR,
    QuadWalk,
)

# Reward re-tuning for the residual setting. The creep values were built for a
# fast freeform gait; against a 0.6 cm/s reference they do not discriminate:
#   * stagnation fires below 1.5 mm/step, i.e. below 0.75 m/s -> disable
#   * the speed term used sigma 0.20, so 0 and 0.12 m/s scored almost the same
#   * the smoothness penalty dominated every other term early in training
_base.PEN_STAGNATION = 0.0
_base.V_TARGET = 0.05        # aim at 5 cm/s, ~8x faster than the open-loop reference
_base.V_SIGMA = 0.03
_base.W_SPEED = 6.0
_base.W_SMOOTH = 0.4
_base.EPISODE_STEPS = 5000   # 10 s, several gait cycles per episode

RESIDUAL_SCALE = 0.35     # max joint correction in rad
W_LATERAL = 0.8           # penalty on sideways drift (X), per metre per step
W_YAW = 0.3               # penalty on heading error (yaw), per radian per step
GAIT_PERIOD = 2.6         # crawl cycle in seconds (the walking configuration)
W_TRACK = 0.5             # pull toward the open-loop reference
W_RES = 0.20              # keep the residual small
LEGS = ("A", "B", "C", "D")


def yaw_of(quat):
    """Yaw angle from a MuJoCo quaternion (w, x, y, z)."""
    w, x, y, z = quat
    return float(np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z)))


class QuadWalkResidual(QuadWalk):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gait = CrawlGait(self.order, self.q0, period=GAIT_PERIOD)
        self.w_creep = 0.0                        # the phase now comes from the gait clock
        n = self.model.nq + self.model.nv + 8
        self.observation_space = spaces.Box(-np.inf, np.inf, shape=(n,), dtype=np.float32)
        self.gait_t = 0.0
        self.q_ref = self.q0.copy()
        self.x0 = 0.0

    def _phase_feats(self):
        ph = np.array([self.gait.leg_phase(leg, self.gait_t) for leg in LEGS])
        two_pi = 2.0 * np.pi * ph
        return np.concatenate([np.sin(two_pi), np.cos(two_pi)]).astype(np.float32)

    def _obs(self):
        return np.concatenate([self.data.qpos, self.data.qvel, self._phase_feats()]).astype(np.float32)

    def reset(self, **kwargs):
        self.gait_t = 0.0
        self.q_ref = self.gait.reference(0.0)
        obs, info = super().reset(**kwargs)
        self.x0 = float(self.data.qpos[0])
        return obs, info

    def _apply_action(self, action):
        a = np.clip(np.asarray(action, dtype=float).ravel(), -1.0, 1.0) * RESIDUAL_SCALE
        target = self.q_ref[:len(a)] + a
        q = self.data.qpos[7:]
        qd = self.data.qvel[6:]
        u = np.zeros(self.model.nu)
        for k, jn in enumerate(self.order):
            v = 40.0 * (target[k] - q[k]) - 4.0 * qd[k]
            if jn.split("-")[0].replace("unit", "") in FRONT:
                v = float(np.clip(v * 1.5, -6.0, 6.0))
            if "PIP" in jn and q[k] < KNEE_FLOOR and v < 0:
                v = 0.0
            u[self.lut[jn]] = v
        self.data.ctrl[:] = np.clip(u, -6, 6)

    def step(self, action):
        self.gait_t += self.model.opt.timestep
        self.q_ref = self.gait.reference(self.gait_t)
        obs, reward, done, trunc, info = super().step(action)
        a = np.clip(np.asarray(action, dtype=float).ravel(), -1.0, 1.0)
        track = float(np.mean(np.abs(self.data.qpos[7:] - self.q_ref)))
        lateral = abs(float(self.data.qpos[0]) - self.x0)
        yaw = abs(yaw_of(self.data.qpos[3:7]))
        reward -= (W_TRACK * track + W_RES * float(np.mean(a * a))
                   + W_LATERAL * lateral + W_YAW * yaw)
        info["lateral"] = lateral
        info["yaw"] = yaw
        return obs, reward, done, trunc, info


def main():
    total = int(sys.argv[1]) if len(sys.argv) > 1 else paths.TRAIN_STEPS_PER_ROUND
    resume = "--resume" in sys.argv
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env

    paths.ensure_dirs()
    env = make_vec_env(QuadWalkResidual, n_envs=paths.N_ENVS)
    last = paths.ckpt("residual", "last")
    kwargs = dict(verbose=1, n_steps=2048, batch_size=512, learning_rate=3e-4,
                  device=paths.DEVICE, policy_kwargs={"net_arch": [256, 256]})
    if resume and os.path.exists(last + ".zip"):
        model = PPO.load(last, env=env, device=paths.DEVICE)
        print("resumed from", last, flush=True)
    else:
        model = PPO("MlpPolicy", env, **kwargs)
    model.learn(total_timesteps=total, reset_num_timesteps=not resume)
    paths.ensure_dirs()
    model.save(last)
    print("saved", last, flush=True)


if __name__ == "__main__":
    main()
