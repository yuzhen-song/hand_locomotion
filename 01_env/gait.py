"""Open-loop crawl gait reference for the 16-DoF hand.

Measured properties of this hand (all numbers from the real model):

  * MCP-FLX is the only joint with meaningful fore-aft authority on the
    fingertip: 0.053 m of Y travel per radian. Its sign is mirrored between
    the two leg pairs: positive FLX moves the tip forward on C/D and backward
    on A/B, so every leg needs its own sign.
  * PIP contributes +-0.027 m/rad in Y and +-0.02 m/rad in X, and a small
    vertical lift (+0.002 m per 0.15 rad) - enough for ground clearance.
  * DIP has no measurable effect on the fingertip, so the reference keeps it
    at the stance value.
  * MCP-ABD is lateral only (0.02 m/rad in X); the reference holds the splay
    that the stance q0 already uses.

Gait: one leg swings at a time, swing order A -> D -> B -> C. The defaults
(period 2.6 s, duty 0.85, stride 0.35 rad, no knee flex) are the configuration
that makes the open-loop reference walk forward on this model - see README.
Per leg the reference sweeps the hip from front to back during stance (the
body is pushed forward over a planted foot) and from back to front during
swing (the foot repositions ahead of the body).
"""
import math

import numpy as np

LEGS = ("A", "B", "C", "D")
SWING_ORDER = ("A", "D", "B", "C")
FORWARD_SIGN = {"C": +1.0, "D": +1.0, "A": -1.0, "B": -1.0}
# Which legs sit on the +X side. Used by the heading controller.
SIDE = {"A": +1.0, "C": +1.0, "B": -1.0, "D": -1.0}

# Phase offset per leg. "crawl" keeps exactly one leg swinging (3&1), "trot"
# swings the diagonal pairs A+D / B+C together (2&2).
PHASE_SETS = {
    "crawl": {"A": 0.00, "D": 0.25, "B": 0.50, "C": 0.75},
    "trot": {"A": 0.00, "D": 0.00, "B": 0.50, "C": 0.50},
    "pace": {"A": 0.00, "C": 0.00, "B": 0.50, "D": 0.50},
    "bound": {"A": 0.00, "B": 0.00, "C": 0.50, "D": 0.50},
}


def yaw_scale(yaw, k=2.0, lo=0.3, hi=1.7):
    """Per-leg stride scale that steers the heading.

    The 2x2 finger layout produces a systematic yaw moment, so the open-loop
    reference turns instead of walking straight. Scaling the stride of the +X
    and -X leg pairs in opposite directions creates a counter moment.
    """
    yaw = max(min(float(yaw), 0.6), -0.6)
    return {leg: float(min(max(1.0 + k * yaw * SIDE[leg], lo), hi)) for leg in LEGS}


def yaw_of(quat):
    """Yaw (rad) from a MuJoCo quaternion (w, x, y, z)."""
    import math
    w, x, y, z = quat
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def heading_of(quat):
    """Heading (rad) about the world Z axis, for the palm's rest frame.

    The mount carries a -90 deg rotation about Y in the URDF, so its local X
    axis is the world up.  ZYX Euler angles are then gimbal-locked (pitch
    sits at -87 deg) and `yaw_of` returns garbage.  The palm's heading is the
    angle of its local Y axis in the world XY plane instead.
    """
    import math
    w, x, y, z = quat
    R01 = 2.0 * (x * y - w * z)
    R11 = 1.0 - 2.0 * (x * x + z * z)
    return math.atan2(-R01, R11)


def _smooth(x):
    """C1 smoothstep, keeps the reference continuous at the phase seams."""
    x = min(max(x, 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


class CrawlGait:
    """Produces a joint-space reference that is aligned with env.order."""

    def __init__(self, order, q0, period=2.6, duty=0.85, stride=0.35, knee=0.0,
                 sweep=1.0, phases=None):
        self.order = list(order)
        self.q0 = np.asarray(q0, dtype=float).copy()
        self.period = float(period)
        self.duty = float(duty)
        self.stride = float(stride)
        self.knee = float(knee)
        # sweep = +1: stance sweeps front->back (body pushed forward)
        # sweep = -1: reversed sweep, for hands whose sign convention differs
        self.sweep = float(sweep)
        self.phases = dict(phases or PHASE_SETS["crawl"])
        self.index = {}
        for k, name in enumerate(self.order):
            leg = name.split("-")[0].replace("unit", "")
            joint = name.split("-", 1)[1]
            self.index[(leg, joint)] = k

    def leg_phase(self, leg, t):
        """Phase of one leg in [0, 1); 0 starts the stance of that leg."""
        return ((t / self.period) + self.phases[leg]) % 1.0

    def reference(self, t, scale=None):
        """Full 16-value joint reference at time t.

        scale: optional per-leg stride multiplier (see yaw_scale) for steering.
        """
        q = self.q0.copy()
        for leg in LEGS:
            amp = self.stride * (1.0 if scale is None else scale.get(leg, 1.0))
            u = self.leg_phase(leg, t)
            if u < self.duty:
                s = 1.0 - _smooth(u / self.duty)   # stance: front -> back
                lift = 0.0
            else:
                v = (u - self.duty) / (1.0 - self.duty)
                s = _smooth(v)                     # swing: back -> front
                lift = math.sin(math.pi * v)        # mid-swing clearance
            if self.sweep < 0:
                s = 1.0 - s
            sign = FORWARD_SIGN[leg]
            k = self.index[(leg, "MCP-FLX")]
            q[k] = self.q0[k] + sign * amp * (2.0 * s - 1.0)
            k = self.index[(leg, "PIP")]
            q[k] = self.q0[k] + self.knee * lift
        return q

    def swing_leg(self, t):
        """Which leg is in the air right now (None if between swings)."""
        for leg in LEGS:
            if self.leg_phase(leg, t) >= self.duty:
                return leg
        return None

    def is_swinging(self, leg, t):
        return self.leg_phase(leg, t) >= self.duty
