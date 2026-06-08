"""Tests for agent homeostasis and gauges."""

import pytest
from si_runtime.agent import Agent


class TestAgent:
    def test_add_gauge(self):
        a = Agent(id="test")
        a.add_gauge("temp", 20.0)
        assert a.gauges["temp"] == 20.0

    def test_homeostasis_converges(self):
        a = Agent(id="thermo")
        a.add_gauge("temp", 10.0)
        # Run homeostasis many times targeting temp=20
        for _ in range(200):
            a.homeostasis({"temp": 20.0}, dt=0.1)
        assert abs(a.gauges["temp"] - 20.0) < 0.5

    def test_homeostasis_ignores_missing_gauge(self):
        a = Agent(id="x")
        a.add_gauge("a", 1.0)
        # "b" not in gauges — should be silently skipped
        a.homeostasis({"b": 10.0})
        assert "b" not in a.gauges
