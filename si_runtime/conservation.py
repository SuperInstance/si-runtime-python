"""Conservation budget management — invariant: gamma + eta == total."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Budget:
    """Top-level conservation budget envelope."""
    total: float
    gamma: float  # spectral budget
    eta: float    # capability budget


@dataclass
class Violation:
    """Records a broken conservation invariant."""
    agent_id: str
    expected: float
    actual: float
    delta: float


@dataclass
class AgentBudget:
    """Per-agent budget tracker."""
    id: str
    budget: Budget
    _allocated: float = 0.0
    _spent: float = 0.0

    def allocate(self, amount: float) -> None:
        if amount < 0:
            raise ValueError(f"cannot allocate negative amount: {amount}")
        if self._allocated + amount > self.budget.total:
            raise ValueError(
                f"allocation {self._allocated + amount} exceeds budget {self.budget.total}"
            )
        self._allocated += amount

    def spend(self, amount: float) -> None:
        if amount < 0:
            raise ValueError(f"cannot spend negative amount: {amount}")
        if self._spent + amount > self._allocated:
            raise ValueError(
                f"spend {self._spent + amount} exceeds allocation {self._allocated}"
            )
        self._spent += amount

    @property
    def remaining(self) -> float:
        return self._allocated - self._spent


def validate_budget(b: Budget) -> bool:
    """Check the conservation invariant: gamma + eta == total."""
    return abs(b.gamma + b.eta - b.total) < 1e-9


def transfer(from_agent: AgentBudget, to_agent: AgentBudget, amount: float) -> None:
    """Move budget between agents, validating the conservation invariant."""
    if amount <= 0:
        raise ValueError(f"transfer amount must be positive: {amount}")
    if from_agent.remaining < amount:
        raise ValueError(
            f"agent {from_agent.id} has insufficient remaining budget: {from_agent.remaining}"
        )
    from_agent.spend(amount)
    to_agent.allocate(amount)
    # Verify invariant still holds on both sides
    for ag in (from_agent, to_agent):
        if not validate_budget(ag.budget):
            raise ValueError(f"conservation invariant violated for agent {ag.id}")


def audit(budgets: list[AgentBudget]) -> list[Violation]:
    """Audit a list of agent budgets, returning any violations."""
    violations: list[Violation] = []
    for ag in budgets:
        b = ag.budget
        actual = b.gamma + b.eta
        if abs(actual - b.total) >= 1e-9:
            violations.append(
                Violation(
                    agent_id=ag.id,
                    expected=b.total,
                    actual=actual,
                    delta=abs(actual - b.total),
                )
            )
    return violations
