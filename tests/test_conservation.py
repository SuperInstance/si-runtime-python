"""Tests for conservation budget management."""

import pytest
from si_runtime.conservation import Budget, AgentBudget, Violation, transfer, audit, validate_budget


class TestBudget:
    def test_valid_budget(self):
        b = Budget(total=10.0, gamma=6.0, eta=4.0)
        assert validate_budget(b) is True

    def test_invalid_budget(self):
        b = Budget(total=10.0, gamma=5.0, eta=3.0)
        assert validate_budget(b) is False


class TestAgentBudget:
    @pytest.fixture
    def agent(self):
        return AgentBudget(id="a1", budget=Budget(total=100.0, gamma=60.0, eta=40.0))

    def test_allocate_and_remaining(self, agent):
        agent.allocate(50.0)
        assert agent.remaining == 50.0

    def test_spend(self, agent):
        agent.allocate(80.0)
        agent.spend(30.0)
        assert agent.remaining == 50.0

    def test_allocate_exceeds_budget(self, agent):
        with pytest.raises(ValueError, match="exceeds budget"):
            agent.allocate(200.0)

    def test_spend_exceeds_allocation(self, agent):
        agent.allocate(10.0)
        with pytest.raises(ValueError, match="exceeds allocation"):
            agent.spend(20.0)

    def test_negative_allocate(self, agent):
        with pytest.raises(ValueError, match="negative"):
            agent.allocate(-5.0)


class TestTransfer:
    def test_transfer_success(self):
        a1 = AgentBudget(id="a1", budget=Budget(total=100.0, gamma=60.0, eta=40.0))
        a2 = AgentBudget(id="a2", budget=Budget(total=100.0, gamma=60.0, eta=40.0))
        a1.allocate(50.0)
        transfer(a1, a2, 20.0)
        assert a1.remaining == 30.0
        assert a2.remaining == 20.0

    def test_transfer_insufficient(self):
        a1 = AgentBudget(id="a1", budget=Budget(total=100.0, gamma=60.0, eta=40.0))
        a2 = AgentBudget(id="a2", budget=Budget(total=100.0, gamma=60.0, eta=40.0))
        a1.allocate(5.0)
        with pytest.raises(ValueError, match="insufficient"):
            transfer(a1, a2, 10.0)


class TestAudit:
    def test_audit_clean(self):
        agents = [
            AgentBudget(id="a1", budget=Budget(total=10.0, gamma=6.0, eta=4.0)),
            AgentBudget(id="a2", budget=Budget(total=20.0, gamma=12.0, eta=8.0)),
        ]
        assert audit(agents) == []

    def test_audit_violation(self):
        agents = [
            AgentBudget(id="bad", budget=Budget(total=10.0, gamma=3.0, eta=3.0)),
        ]
        violations = audit(agents)
        assert len(violations) == 1
        assert violations[0].agent_id == "bad"
