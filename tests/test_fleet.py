"""Tests for fleet orchestration."""

import pytest
from si_runtime.fleet import Fleet
from si_runtime.agent import Agent
from si_runtime.conservation import Budget, AgentBudget


class TestFleet:
    def test_add_agent(self):
        f = Fleet()
        f.add_agent(Agent(id="a1"))
        assert len(f.agents) == 1

    def test_spectral_rank_no_adjacency(self):
        f = Fleet()
        f.add_agent(Agent(id="a1"))
        f.add_agent(Agent(id="a2"))
        assert f.spectral_rank() == [0, 1]

    def test_spectral_rank_with_adjacency(self):
        # 4-node line: 0-1-2-3 — nodes 1 and 2 are more central
        f = Fleet(
            adjacency=[
                [0.0, 1.0, 0.0, 0.0],
                [1.0, 0.0, 1.0, 0.0],
                [0.0, 1.0, 0.0, 1.0],
                [0.0, 0.0, 1.0, 0.0],
            ]
        )
        for i in range(4):
            f.add_agent(Agent(id=f"n{i}"))
        rank = f.spectral_rank()
        # Interior nodes (1, 2) should rank before leaf nodes (0, 3)
        assert rank[0] in (1, 2)

    def test_conservation_audit(self):
        f = Fleet()
        f.add_agent(
            Agent(id="ok"),
            AgentBudget(id="ok", budget=Budget(total=10.0, gamma=6.0, eta=4.0)),
        )
        f.add_agent(
            Agent(id="bad"),
            AgentBudget(id="bad", budget=Budget(total=10.0, gamma=3.0, eta=3.0)),
        )
        violations = f.conservation_audit()
        assert len(violations) == 1
        assert violations[0].agent_id == "bad"

    def test_health_report(self):
        f = Fleet()
        a = Agent(id="a")
        a.add_gauge("cpu", 0.5)
        f.add_agent(a)
        report = f.health_report()
        assert report["agent_count"] == 1
        assert report["conservation_violations"] == 0
        assert report["total_gauges"] == 1
