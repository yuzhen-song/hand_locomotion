"""Cascaded controller for the hand's trot gait.

Three levels, slowest outermost:

    feedforward   constant stride bias that cancels the mean sideways drift
    inner loop    P on the body yaw (~1 s): the left/right legs take different
                  strides so the body spin is damped
    outer loop    P on the low-passed lateral position (~4 s): shifts the bias
                  so the accumulated sideways error is driven back to zero

The two loops run on different time scales on purpose.  When the outer loop acts
on the raw position the two fight each other and the gait destabilises; a 4 s
low-pass on the outer error decouples them (see README).

`targets()` is the whole interface: feed it the base qpos and the elapsed time,
get back the joint targets to hand to a PD loop.
"""

import math
import numpy as np

from gait import PHASE_SETS, SIDE, CrawlGait, heading_of


class TrotController:
    def __init__(self, order, q0, period=1.6, duty=0.5, stride=0.6, knee=0.4,
                 phases="trot", bias=-0.10, yaw_gain=-0.20, lat_gain=-2.0, lat_tau=4.0):
        self.gait = CrawlGait(order, q0, period=period, duty=duty, stride=stride,
                              knee=knee, phases=PHASE_SETS[phases])
        self.bias = float(bias)
        self.yaw_gain = float(yaw_gain)
        self.lat_gain = float(lat_gain)
        self.lat_tau = float(lat_tau)
        self.legs = ("A", "B", "C", "D")
        self.reset(0.0, 0.0)

    def reset(self, x0, y0):
        self.x0 = float(x0)
        self.y0 = float(y0)
        self._lat_f = 0.0   # low-passed lateral error
        self.last_scales = {leg: 1.0 for leg in self.legs}

    def _scales(self, qpos, dt):
        xerr = float(qpos[0]) - self.x0
        if self.lat_tau > 0:
            alpha = math.exp(-dt / self.lat_tau)
            self._lat_f = alpha * self._lat_f + (1.0 - alpha) * xerr
            xerr = self._lat_f
        yaw = heading_of(qpos[3:7])
        yaw = float(np.arctan2(np.sin(yaw), np.cos(yaw)))
        corr = float(np.clip(self.yaw_gain * yaw, -0.4, 0.4))
        beff = float(np.clip(self.bias + self.lat_gain * xerr, -0.7, 0.7))
        self.last_scales = {leg: float(np.clip((1.0 - beff * SIDE[leg]) * (1.0 + corr * SIDE[leg]),
                                               0.35, 1.75))
                            for leg in self.legs}
        return self.last_scales

    def targets(self, t, qpos, dt):
        return self.gait.reference(t, self._scales(qpos, dt))
