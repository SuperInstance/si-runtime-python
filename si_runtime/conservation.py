"""Conservation budget enforcement.

The invariant: gamma (kinetic) + eta (potential) = total (constant).
Any operation that would violate this returns a ConservationError.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


class ConservationError(Exception):
    """Raised when gamma + eta != total after an operation."""
    pass


@dataclass(frozen=True)
class Budget:
    """Immutable conservation budget."""
    gamma: float   # kinetic / active energy
    eta: float     # potential / reserve energy
    total: float   # constant C = gamma + eta

    def __post_init__(self):
        if not _approx_eq(self.gamma + self.eta, self.total):
            raise ConservationError(
                f"Invariant broken: {self.gamma} + {self.eta} != {self.total}"
            )
        if self.gamma < 0 or self.eta < 0:
            raise ConservationError("Energy components must be non-negative")

    @staticmethod
    def create(total: float) -> "Budget":
        """Create a fresh budget with energy split evenly."""
        return Budget(gamma=total / 2.0, eta=total / 2.0, total=total)


@dataclass
class AgentBudget:
    """Mutable per-agent budget wrapper."""
    gamma: float
    eta: float
    total: float

    @staticmethod
    def create(total: float) -> "AgentBudget":
        return AgentBudget(gamma=total / 2.0, eta=total / 2.0, total=total)

    def _check(self) -> None:
        if not _approx_eq(self.gamma + self.eta, self.total):
            raise ConservationError(
                f"Invariant broken: {self.gamma} + {self.eta} != {self.total}"
            )
        if self.gamma < 0 or self.eta < 0:
            raise ConservationError("Energy components must be non-negative")


@dataclass(frozen=True)
class Audit:
    """Result of a conservation audit."""
    gamma: float
    eta: float
    total: float
    utilization: float
    valid: bool


def allocate(budget: AgentBudget, gamma: float, eta: float) -> None:
    """Reallocate energy between gamma and eta."""
    if gamma < 0 or eta < 0:
        raise ConservationError("Cannot allocate negative energy")
    if not _approx_eq(gamma + eta, budget.total):
        raise ConservationError(
            f"Allocation must sum to total {budget.total}, got {gamma + eta}"
        )
    budget.gamma = gamma
    budget.eta = eta
    budget._check()


def transfer(budget: AgentBudget, from_gamma: bool, amount: float) -> None:
    """Transfer amount from gamma to eta (or reverse)."""
    if amount < 0:
        raise ConservationError("Cannot transfer negative amount")
    if from_gamma:
        if budget.gamma < amount:
            raise ConservationError("Insufficient gamma energy")
        budget.gamma -= amount
        budget.eta += amount
    else:
        if budget.eta < amount:
            raise ConservationError("Insufficient eta energy")
        budget.eta -= amount
        budget.gamma += amount
    budget._check()


def audit(budget: AgentBudget) -> Audit:
    """Audit the budget and return a report."""
    try:
        budget._check()
        valid = True
    except ConservationError:
        valid = False

    utilization = 0.0
    if budget.total > 0:
        utilization = 1.0 - (budget.gamma + budget.eta - abs(budget.gamma - budget.eta)) / (2.0 * budget.total)

    return Audit(
        gamma=budget.gamma,
        eta=budget.eta,
        total=budget.total,
        utilization=utilization,
        valid=valid,
    )


def _approx_eq(a: float, b: float, tol: float = 1e-9) -> bool:
    return abs(a - b) <= tol
