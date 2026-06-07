"""Pytest suite for si_runtime — 15+ tests covering all modules."""

import math
import pytest

from si_runtime import (
    Budget,
    AgentBudget,
    allocate,
    transfer,
    audit,
    AdjacencyMatrix,
    power_iteration,
    spectral_rank,
    Capability,
    Registry,
    match_capabilities,
    Cell,
    Agent,
    Fleet,
)
from si_runtime.conservation import ConservationError
from si_runtime.agent import AgentState, HomeostasisError


# ---------------------------------------------------------------------------
# Conservation
# ---------------------------------------------------------------------------

class TestBudget:
    def test_budget_create(self):
        b = Budget.create(100.0)
        assert b.gamma == 50.0
        assert b.eta == 50.0
        assert b.total == 100.0

    def test_budget_invariant_enforced(self):
        with pytest.raises(ConservationError):
            Budget(gamma=60.0, eta=60.0, total=100.0)

    def test_budget_negative_energy(self):
        with pytest.raises(ConservationError):
            Budget(gamma=-10.0, eta=110.0, total=100.0)


class TestAgentBudget:
    def test_allocate(self):
        b = AgentBudget.create(100.0)
        allocate(b, 30.0, 70.0)
        assert b.gamma == 30.0
        assert b.eta == 70.0

    def test_allocate_overflow(self):
        b = AgentBudget.create(100.0)
        with pytest.raises(ConservationError):
            allocate(b, 60.0, 60.0)

    def test_transfer(self):
        b = AgentBudget.create(100.0)
        transfer(b, from_gamma=True, amount=10.0)
        assert math.isclose(b.gamma, 40.0, abs_tol=1e-9)
        assert math.isclose(b.eta, 60.0, abs_tol=1e-9)

    def test_transfer_reverse(self):
        b = AgentBudget.create(100.0)
        transfer(b, from_gamma=False, amount=10.0)
        assert math.isclose(b.gamma, 60.0, abs_tol=1e-9)
        assert math.isclose(b.eta, 40.0, abs_tol=1e-9)

    def test_transfer_overdraft(self):
        b = AgentBudget.create(100.0)
        with pytest.raises(ConservationError):
            transfer(b, from_gamma=True, amount=100.0)

    def test_audit(self):
        b = AgentBudget.create(100.0)
        allocate(b, 40.0, 60.0)
        r = audit(b)
        assert r.valid
        assert r.gamma == 40.0
        assert r.eta == 60.0
        assert r.total == 100.0


# ---------------------------------------------------------------------------
# Spectral
# ---------------------------------------------------------------------------

class TestSpectral:
    def test_adjacency_matrix_square(self):
        m = AdjacencyMatrix([[1.0, 0.5], [0.5, 1.0]])
        assert m.size == 2

    def test_adjacency_matrix_not_square(self):
        with pytest.raises(ValueError):
            AdjacencyMatrix([[1.0, 0.5], [0.5]])

    def test_power_iteration(self):
        m = AdjacencyMatrix([[4.0, 1.0], [1.0, 3.0]])
        ev, vec = power_iteration(m, iterations=300)
        assert ev > 0
        assert len(vec) == 2
        # Dominant eigenvalue should be ~4.618
        assert math.isclose(ev, 4.618, abs_tol=0.1)

    def test_spectral_rank(self):
        m = AdjacencyMatrix([
            [5.0, 0.0, 0.0],
            [0.0, 2.0, 0.0],
            [0.0, 0.0, 1.0],
        ])
        ranked = spectral_rank(m)
        assert len(ranked) == 3
        # Largest eigenvalue first
        assert ranked[0][0] == 0

    def test_spectral_rank_identity(self):
        m = AdjacencyMatrix([[1.0, 0.0], [0.0, 1.0]])
        ranked = spectral_rank(m)
        assert len(ranked) == 2
        # Both eigenvalues are 1.0
        assert math.isclose(abs(ranked[0][1]), 1.0, abs_tol=0.1)


# ---------------------------------------------------------------------------
# Capability
# ---------------------------------------------------------------------------

class TestCapability:
    def test_capability_matches(self):
        a = Capability("plan", tags=("nav",))
        b = Capability("plan", tags=("nav", "exec"))
        assert b.matches(a)
        assert not a.matches(b)  # a lacks "exec"

    def test_registry(self):
        reg = Registry()
        cap = Capability("vision", tags=("camera",))
        reg.register(cap, "agent_1")
        assert "vision" in reg
        assert reg.owners("vision") == {"agent_1"}

    def test_match_capabilities(self):
        required = [Capability("plan"), Capability("sense")]
        offered = [Capability("plan"), Capability("move")]
        matched, unmatched = match_capabilities(required, offered)
        assert len(matched) == 1
        assert len(unmatched) == 1
        assert unmatched[0].name == "sense"


# ---------------------------------------------------------------------------
# Cell
# ---------------------------------------------------------------------------

class TestCell:
    def test_cell_update(self):
        c = Cell("a", state=1.0)
        c.update(lambda cell, neighbors: cell.state + 1.0)
        assert c.state == 2.0

    def test_cell_neighbors(self):
        a = Cell("a", state=1.0)
        b = Cell("b", state=2.0)
        a.add_neighbor(b)
        assert a.degree == 1
        assert b.degree == 1  # bidirectional
        assert math.isclose(a.mean_field(), 2.0)

    def test_cell_energy(self):
        c = Cell("a", state=0.0, energy_cost=0.05)
        c.update(lambda cell, neighbors: 1.0)
        c.update(lambda cell, neighbors: 2.0)
        assert math.isclose(c.energy_spent(), 0.10, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

class TestAgent:
    def test_agent_init(self):
        a = Agent("bot_1")
        assert a.agent_id == "bot_1"
        assert a.state == AgentState.IDLE
        assert a.gamma_ratio == 0.5

    def test_agent_spend(self):
        a = Agent("bot_1", budget=AgentBudget.create(100.0))
        a.spend(10.0)
        assert math.isclose(a.budget.gamma, 40.0, abs_tol=1e-9)
        assert math.isclose(a.budget.eta, 60.0, abs_tol=1e-9)

    def test_agent_stressed(self):
        a = Agent("bot_1", budget=AgentBudget.create(100.0), critical_gamma_ratio=0.5)
        a.spend(30.0)  # gamma now 20, ratio 0.2
        assert a.state == AgentState.STRESSED

    def test_agent_activate_stressed(self):
        a = Agent("bot_1", budget=AgentBudget.create(100.0), critical_gamma_ratio=0.5)
        a.spend(30.0)
        with pytest.raises(HomeostasisError):
            a.activate()

    def test_agent_capability(self):
        a = Agent("bot_1", capabilities=[Capability("plan"), Capability("see")])
        assert a.has_capability("plan")
        assert not a.has_capability("fly")
        assert a.capability_names() == {"plan", "see"}


# ---------------------------------------------------------------------------
# Fleet
# ---------------------------------------------------------------------------

class TestFleet:
    def test_fleet_add_remove(self):
        f = Fleet("test")
        a = Agent("a1")
        f.add_agent(a)
        assert f.size == 1
        assert "a1" in f
        removed = f.remove_agent("a1")
        assert removed is not None
        assert f.size == 0

    def test_fleet_rank(self):
        f = Fleet("test")
        a1 = Agent("a1", capabilities=[Capability("plan"), Capability("see")])
        a2 = Agent("a2", capabilities=[Capability("plan"), Capability("fly")])
        f.add_agent(a1)
        f.add_agent(a2)
        ranked = f.spectral_rank()
        assert len(ranked) == 2
        # Both have "plan" in common

    def test_fleet_health(self):
        f = Fleet("test")
        a1 = Agent("a1", budget=AgentBudget.create(100.0))
        f.add_agent(a1)
        health = f.fleet_health()
        assert health["agents"] == 1
        assert health["status"] == "healthy"

    def test_fleet_conservation_audit(self):
        f = Fleet("test")
        a1 = Agent("a1", budget=AgentBudget.create(100.0))
        f.add_agent(a1)
        audits = f.conservation_audit()
        assert "a1" in audits
        assert audits["a1"].valid
