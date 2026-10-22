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


def _smooth(x):
    """C1 smoothstep, keeps the reference continuous at the phase seams."""
    x = min(max(x, 0.0), 1.0)
    return x * x * (3.0 - 2.0 * x)


class CrawlGait:
    """Produces a joint-space reference that is aligned with env.order."""

    def __init__(self, order, q0, period=2.6, duty=0.85, stride=0.35, knee=0.0, sweep=1.0):
        self.order = list(order)
        self.q0 = np.asarray(q0, dtype=float).copy()
        self.period = float(period)
        self.duty = float(duty)
        self.stride = float(stride)
        self.knee = float(knee)
        # sweep = +1: stance sweeps front->back (body pushed forward)
        # sweep = -1: reversed sweep, for hands whose sign convention differs
        self.sweep = float(sweep)
        self.index = {}
        for k, name in enumerate(self.order):
            leg = name.split("-")[0].replace("unit", "")
            joint = name.split("-", 1)[1]
            self.index[(leg, joint)] = k

    def leg_phase(self, leg, t):
        """Phase of one leg in [0, 1); 0 starts the stance of that leg."""
        off = SWING_ORDER.index(leg) / float(len(SWING_ORDER))
        return ((t / self.period) + off) % 1.0

    def reference(self, t):
        """Full 16-value joint reference at time t."""
        q = self.q0.copy()
        for leg in LEGS:
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
            q[k] = self.q0[k] + sign * self.stride * (2.0 * s - 1.0)
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
