"""Crawl gait environment (main): 16-joint hand walking along +Y, legs cycle A->D->B->C.

Conventions:
  travel direction = +Y (this hand can only crab sideways, it cannot advance along X)
  front legs     = A, B (largest Y)
  joints        = 4 per finger: MCP-FLX(side) / MCP-ABD(fore-aft) / PIP(knee) / DIP(ankle)

Usage:
  python 01_env/train_quad_creep.py 30000          # train from scratch
  python 01_env/train_quad_creep.py 30000 --resume  # resume from 04_checkpoints/creep_last
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths

import mujoco
import numpy as np
import gymnasium as gym
from gymnasium import spaces

XML = paths.MODEL_XML
FRONT = ("A", "B")
TIP_OF = {"C": "finger_tip", "A": "finger_tip_2", "B": "finger_tip_3", "D": "finger_tip_4"}
DIP_OF = {"C": "dip_spacer", "A": "dip_spacer_2", "B": "dip_spacer_3", "D": "dip_spacer_4"}

STANCE = {"MCP-FLX": -1.1, "MCP-ABD": 0.0, "PIP": 1.6, "DIP": -0.8}
ABD_SPLAY = {"C": 0.63, "A": -0.63, "B": 0.63, "D": -0.63}

V_TARGET = 0.12          # target speed m/s (stability first, keep it low)
V_SIGMA = 0.20
W_SPEED = 3.0
W_PROGRESS = 40.0        # reward per unit of forward progress
BONUS_ALIVE = 0.02
PEN_STAGNATION = 0.8     # penalty when the body stops advancing
W_TILT = 12.0
W_BAD_CONTACT = 0.5
W_CENTER = 1.5
W_KNEE = 3.0
KNEE_FLOOR = 0.6
W_SMOOTH = 1.5
W_SWING = 0.3
W_CREEP = 6.0
CLOCK_HZ = 0.35          # crawl clock frequency (slow)
W_TIPDIR = 4.0
W_ACTION = 0.01
PEN_FALL = 20.0
EPISODE_STEPS = 2000


class QuadWalk(gym.Env):
    def __init__(self):
        self.model = mujoco.MjModel.from_xml_path(XML)
        self.data = mujoco.MjData(self.model)
        jnts = [mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_JOINT, i) or "f" for i in range(self.model.njnt)]
        self.order = [j for j in jnts if j and "unit" in j]
        acts = [mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, i) for i in range(self.model.nu)]
        self.lut = {a.replace("m_", ""): i for i, a in enumerate(acts)}

        q0 = np.array([
            STANCE["MCP-FLX"] if "MCP-FLX" in n
            else STANCE["MCP-ABD"] if "MCP-ABD" in n
            else STANCE["PIP"] if "PIP" in n
            else STANCE["DIP"]
            for n in self.order
        ])
        for k, n in enumerate(self.order):
            if "MCP-ABD" in n:
                q0[k] = ABD_SPLAY[n.split("-")[0].replace("unit", "")]
        self.q0 = q0

        self.observation_space = spaces.Box(-np.inf, np.inf,
                                            shape=(self.model.nq + self.model.nv,), dtype=np.float32)
        self.action_space = spaces.Box(-1.0, 1.0, shape=(self.model.nu,), dtype=np.float32)
        self.w_creep = W_CREEP

    def _obs(self):
        return np.concatenate([self.data.qpos, self.data.qvel]).astype(np.float32)

    def _settle(self, steps=200):
        """Settle at spawn: remove residual velocity and contact penetration."""
        for _ in range(steps):
            q = self.data.qpos[7:].copy()
            qd = self.data.qvel[6:].copy()
            u = np.zeros(self.model.nu)
            for k, jn in enumerate(self.order):
                u[self.lut[jn]] = 40.0 * (self.q0[k] - q[k]) - 4.0 * qd[k]
            self.data.ctrl[:] = np.clip(u, -4, 4)
            mujoco.mj_step(self.model, self.data)

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        mujoco.mj_resetData(self.model, self.data)
        self.data.qpos[2] = 0.14
        self.data.qpos[7:] = self.q0.copy()
        mujoco.mj_forward(self.model, self.data)
        self._settle()
        mujoco.mj_forward(self.model, self.data)
        self.prev_a = np.zeros(self.model.nu)
        self.steps = 0
        self.prev_x = float(self.data.qpos[1])
        return self._obs(), {}

    def _apply_action(self, action):
        u = np.zeros(self.model.nu)
        a = np.clip(action, -1, 1) * 4.0
        q_now = self.data.qpos[7:].copy()
        for k, jn in enumerate(self.order):
            leg = jn.split("-")[0].replace("unit", "")
            v = float(a[k]) if k < len(a) else 0.0
            if leg in FRONT:
                v = float(np.clip(v * 1.5, -6.0, 6.0))
            # Hard constraint: a knee near its floor may extend but not fold (torque-level safety filter)
            if "PIP" in jn and q_now[k] < KNEE_FLOOR and v < 0:
                v = 0.0
            u[self.lut[jn]] = v
        self.data.ctrl[:] = np.clip(u, -6, 6)

    def _bad_contacts(self):
        bad = 0
        for i in range(self.data.ncon):
            c = self.data.contact[i]
            g1 = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, c.geom1) or ""
            g2 = mujoco.mj_id2name(self.model, mujoco.mjtObj.mjOBJ_GEOM, c.geom2) or ""
            if "floor" in (g1, g2):
                other = g2 if "floor" in g1 else g1
                if "tip_collision" not in other:
                    bad += 1
        return bad

    def _creep_clock(self):
        """Crawl clock: one full cycle at 0.35 Hz, each leg takes a turn as the swing leg."""
        cyc = (self.steps * self.model.opt.timestep * CLOCK_HZ) % 1.0
        sw_leg = ("A", "D", "B", "C")[int(cyc * 4) % 4]
        score = 0.0
        for leg, body in TIP_OF.items():
            hz = float(self.data.body(body).xpos[2])
            if leg == sw_leg:
                score += min(max(hz - 0.03, 0.0), 0.05)
            else:
                score += min(max(0.03 - hz, 0.0), 0.03) * 0.5
        return score

    def _tip_upright_violations(self):
        """The DIP-to-tip segment must point downwards; pointing up is a violation."""
        n = 0
        for leg in TIP_OF:
            v = np.array(self.data.body(TIP_OF[leg]).xpos) - np.array(self.data.body(DIP_OF[leg]).xpos)
            norm = max(float(np.linalg.norm(v)), 1e-6)
            if v[2] > -0.5 * norm:
                n += 1
        return n

    def step(self, action):
        self._apply_action(action)
        mujoco.mj_step(self.model, self.data)
        self.steps += 1

        R = np.array(self.data.body("platform_mount").xmat).reshape(3, 3)
        up_z = float(R[2, 0])  # vertical component: third element of R[:,0]
        alive = up_z > 0.7 and self.data.qpos[2] > 0.05
        vx = float(self.data.qvel[1])
        x = float(self.data.qpos[1])
        dx_step = x - self.prev_x
        self.prev_x = x

        tilt_penalty = W_TILT * max(0.0, 0.99 - up_z)
        stagnation = PEN_STAGNATION if abs(dx_step) < 0.0015 else 0.0
        center_dev = float(np.mean(np.abs(self.data.qpos[7:] - self.q0)))
        all_pip = [float(self.data.qpos[7:][k]) for k, jn in enumerate(self.order) if "PIP" in jn]
        knee_fold = max(0.0, KNEE_FLOOR - min(all_pip)) if all_pip else 0.0
        smooth = float(np.mean(np.square(np.array(action, dtype=float).ravel() - self.prev_a)))
        self.prev_a = np.array(action, dtype=float).ravel()
        swing = float(np.mean(np.abs(self.data.qvel[6:])))

        reward = (
            W_SPEED * float(np.exp(-((vx - V_TARGET) / V_SIGMA) ** 2))
            + W_PROGRESS * dx_step
            + (BONUS_ALIVE if alive else 0.0)
            - stagnation
            - tilt_penalty
            - W_BAD_CONTACT * self._bad_contacts()
            - W_CENTER * max(0.0, center_dev - 0.35)
            - W_KNEE * knee_fold
            - W_SMOOTH * smooth
            + W_SWING * min(swing, 2.0)
            + self.w_creep * self._creep_clock()
            - W_TIPDIR * self._tip_upright_violations()
            - W_ACTION * float(np.sum(np.square(action)))
        )

        done = (not alive) or self.steps >= EPISODE_STEPS
        if not alive:
            reward -= PEN_FALL
        return self._obs(), float(reward), done, False, {"x": x}


def main():
    total = int(sys.argv[1]) if len(sys.argv) > 1 else paths.TRAIN_STEPS_PER_ROUND
    resume = "--resume" in sys.argv
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env

    paths.ensure_dirs()
    env = make_vec_env(QuadWalk, n_envs=paths.N_ENVS)
    last = paths.ckpt("creep", "last")
    kwargs = dict(verbose=1, n_steps=2048, batch_size=512, learning_rate=3e-4,
                  device=paths.DEVICE, policy_kwargs={"net_arch": [256, 256]})
    if resume and os.path.exists(last + ".zip"):
        model = PPO.load(last, env=env, device=paths.DEVICE)
        print("resumed from", last, flush=True)
    else:
        model = PPO("MlpPolicy", env, **kwargs)
    model.learn(total_timesteps=total, reset_num_timesteps=not resume)
    model.save(last)
    print("saved", last)


if __name__ == "__main__":
    main()
