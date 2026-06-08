"""Agent with state, capabilities, and PID-gauged homeostasis."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .capability import Capability


@dataclass
class Agent:
    """An autonomous agent with state, capabilities, and homeostatic gauges."""
    id: str
    state: dict[str, Any] = field(default_factory=dict)
    capabilities: list[Capability] = field(default_factory=list)
    gauges: dict[str, float] = field(default_factory=dict)
    _integral: dict[str, float] = field(default_factory=dict, repr=False)
    _prev_error: dict[str, float] = field(default_factory=dict, repr=False)

    def add_gauge(self, name: str, value: float) -> None:
        self.gauges[name] = value
        self._integral[name] = 0.0
        self._prev_error[name] = 0.0

    def homeostasis(self, targets: dict[str, float], dt: float = 1.0) -> None:
        """PID regulation: adjust gauges toward targets.

        Uses default PID gains (Kp=1.0, Ki=0.1, Kd=0.05).
        """
        kp, ki, kd = 1.0, 0.05, 0.02
        for name, target in targets.items():
            if name not in self.gauges:
                continue
            error = target - self.gauges[name]
            self._integral[name] = self._integral.get(name, 0.0) + error * dt
            # Anti-windup: clamp integral
            self._integral[name] = max(-10.0, min(10.0, self._integral[name]))
            derivative = (error - self._prev_error.get(name, 0.0)) / max(dt, 1e-9)
            adjustment = kp * error + ki * self._integral[name] + kd * derivative
            # Clamp adjustment to prevent divergence
            adjustment = max(-5.0, min(5.0, adjustment))
            self.gauges[name] += adjustment
            self._prev_error[name] = error
