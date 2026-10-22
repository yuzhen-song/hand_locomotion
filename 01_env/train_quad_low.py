"""Free gait environment (control): identical model and reward to creep, crawl clock disabled.

Purpose: head-to-head comparison - creep walks a regular crawl, low lets the policy improvise.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import paths  # noqa: E402

from train_quad_creep import QuadWalk as _CreepEnv  # noqa: E402

NAME = "low"


class QuadWalk(_CreepEnv):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.w_creep = 0.0


def main():
    total = int(sys.argv[1]) if len(sys.argv) > 1 else paths.TRAIN_STEPS_PER_ROUND
    resume = "--resume" in sys.argv
    from stable_baselines3 import PPO
    from stable_baselines3.common.env_util import make_vec_env

    paths.ensure_dirs()
    env = make_vec_env(QuadWalk, n_envs=paths.N_ENVS)
    last = paths.ckpt(NAME, "last")
    if resume and os.path.exists(last + ".zip"):
        model = PPO.load(last, env=env, device=paths.DEVICE)
        print("resumed from", last, flush=True)
    else:
        model = PPO("MlpPolicy", env, verbose=1, n_steps=2048, batch_size=512,
                    learning_rate=3e-4, device=paths.DEVICE,
                    policy_kwargs={"net_arch": [256, 256]})
    model.learn(total_timesteps=total, reset_num_timesteps=not resume)
    model.save(last)
    print("saved", last)


if __name__ == "__main__":
    main()
