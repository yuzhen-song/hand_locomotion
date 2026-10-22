"""Deployment self-check: one command tells whether a new machine can run this project.

Each check runs in its own subprocess so one failure cannot take down the others.

Usage: python 07_tools/doctor.py
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import paths  # noqa: E402

OK, BAD, WARN = "[OK]  ", "[FAIL]", "[WARN]"

CHECKS = [
    ("Python", "import sys; print(f'{sys.version.split()[0]} | {sys.executable}')"),
    ("dependencies", "import mujoco,numpy,gymnasium,imageio,stable_baselines3,torch as t;"
              "print(f'mujoco {mujoco.__version__} | numpy {numpy.__version__} | "
              "gymnasium {gymnasium.__version__} | imageio {imageio.__version__} | "
              "sb3 {stable_baselines3.__version__} | torch {t.__version__}')"),
    ("GPU", "import torch;"
            "print(f'{torch.cuda.get_device_name(0)} | "
            "{torch.cuda.get_device_properties(0).total_memory/2**30:.1f} GiB | "
            "cuda {torch.version.cuda}' if torch.cuda.is_available() "
            "else 'no GPU, training will use cpu (works, but 5-10x slower'))"),
    ("physics model", "import mujoco,paths; m=mujoco.MjModel.from_xml_path(paths.MODEL_XML);"
                 "print(f'nq={m.nq} nu={m.nu} ngeom={m.ngeom} nbody={m.nbody}')"),
    ("mesh assets", "import os,paths; p=os.path.join(paths.MODEL_DIR,'my-robot','assets');"
                 "print(f'{len(os.listdir(p))} files')"),
    ("environment", "import paths,train_quad_creep as T; e=T.QuadWalk(); o,_=e.reset(seed=0);"
                 "o,r,d,tr,i=e.step(e.action_space.sample());"
                 "print(f'obs={o.shape} act={e.action_space.shape} r={r:.2f}')"),
    ("rendering backend", "import os,mujoco,paths; m=mujoco.MjModel.from_xml_path(paths.MODEL_XML);"
                 "d=mujoco.MjData(m); mujoco.mj_forward(m,d);"
                 "r=mujoco.Renderer(m,height=96,width=128); r.update_scene(d);"
                 "img=r.render();"
                 "print(f\"MUJOCO_GL={os.environ.get('MUJOCO_GL','unset')} std={float(img.std()):.1f}\")"),
    ("checkpoints", "import os,paths; from stable_baselines3 import PPO;"
                   "out=[];"
                   "[out.append(f'{n}/{k}') for n in ('creep','low') for k in ('last','best') "
                   "if os.path.exists(paths.ckpt(n,k)+'.zip') and (PPO.load(paths.ckpt(n,k),device='cpu') or True)];"
                   "print(', '.join(out) if out else 'none (training will start from scratch'))"),
    ("evaluation", "import paths; from rollout_measure import measure;"
                   "dx,_=measure('creep','best',verbose=False);"
                   "print(f'creep_best dx={dx:.3f}m(expected ~0.679)')"),
]


SOFT = {"rendering backend", "evaluation", "GPU"}


def run(code, timeout=180, env_extra=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    p = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                       text=True, timeout=timeout, env=env)
    out = (p.stdout + p.stderr).strip().splitlines()
    return p.returncode, (out[-1] if out else "(no output)")


def main():
    print("=" * 64)
    print("hand_locomotion deployment self-check")
    print("=" * 64)
    failed = []
    for label, code in CHECKS:
        try:
            rc, msg = run(code)
        except subprocess.TimeoutExpired:
            rc, msg = 1, "timed out (180s)"
        if rc != 0 and label == "rendering backend":
            for backend in ("wgl", "glfw", "osmesa") if os.name == "nt" else ("osmesa", "glfw"):
                try:
                    rc, msg = run(code, env_extra={"MUJOCO_GL": backend})
                except subprocess.TimeoutExpired:
                    rc, msg = 1, "timed out (180s)"
                if rc == 0:
                    break
        if label == "rendering backend" and rc == 0 and "std=" in msg:
            try:
                if float(msg.split("std=")[1]) < 1.0:
                    print(f"{WARN} {label}: {msg}    <- black screen, try MUJOCO_GL=osmesa")
                    continue
            except Exception:
                pass
        if label == "GPU" and rc == 0 and "no GPU" in msg:
            print(f"{WARN} {label}: {msg}")
            continue
        if rc == 0:
            print(f"{OK} {label}: {msg}")
        elif label in SOFT:
            hint = " (killed by the OS: out of GPU/memory, or backend unavailable)" if not msg.strip() or msg == "(no output)" else ""
            print(f"{WARN} {label}: {msg}{hint}")
        else:
            print(f"{BAD} {label}: {msg}")
            failed.append(label)
    print("=" * 64)
    if failed:
        print(f"failed {len(failed)} checks: {', '.join(failed)}")
        sys.exit(1)
    print("all checks passed, ready to train.")


if __name__ == "__main__":
    main()
