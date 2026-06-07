"""Agent with homeostasis — stateful entity with capabilities and energy budget."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Set

from .conservation import AgentBudget, allocate, transfer, audit
from .capability import Capability


class AgentState(Enum):
    IDLE = auto()
    ACTIVE = auto()
    STRESSED = auto()
    RECOVERING = auto()
    HALTED = auto()


class HomeostasisError(Exception):
    pass


@dataclass
class Agent:
    """An agent with an ID, state machine, capabilities, and energy budget.

    Homeostasis keeps the agent within safe operating bounds.
    If gamma drops below a critical threshold, the agent enters STRESSED
    and must RECOVER before becoming ACTIVE again.
    """
    agent_id: str
    budget: AgentBudget = field(default_factory=lambda: AgentBudget.create(100.0))
    state: AgentState = AgentState.IDLE
    capabilities: List[Capability] = field(default_factory=list)
    _metadata: Dict[str, str] = field(default_factory=dict, repr=False)

    # Homeostasis thresholds
    critical_gamma_ratio: float = 0.1   # gamma/total below this → STRESSED
    recovery_gamma_ratio: float = 0.3   # gamma/total above this → recover

    @property
    def gamma_ratio(self) -> float:
        if self.budget.total <= 0:
            return 0.0
        return self.budget.gamma / self.budget.total

    def tick(self) -> None:
        """Advance one time step, checking homeostasis."""
        if self.state == AgentState.HALTED:
            return

        ratio = self.gamma_ratio

        if ratio < self.critical_gamma_ratio:
            self.state = AgentState.STRESSED
        elif self.state == AgentState.STRESSED and ratio >= self.recovery_gamma_ratio:
            self.state = AgentState.RECOVERING
        elif self.state == AgentState.RECOVERING and ratio >= self.recovery_gamma_ratio:
            self.state = AgentState.IDLE

    def activate(self) -> None:
        if self.state == AgentState.HALTED:
            raise HomeostasisError("Agent is halted")
        if self.state == AgentState.STRESSED:
            raise HomeostasisError("Agent is stressed — cannot activate")
        self.state = AgentState.ACTIVE

    def deactivate(self) -> None:
        if self.state != AgentState.HALTED:
            self.state = AgentState.IDLE

    def halt(self) -> None:
        self.state = AgentState.HALTED

    def has_capability(self, cap_name: str) -> bool:
        return any(c.name == cap_name for c in self.capabilities)

    def capability_names(self) -> Set[str]:
        return {c.name for c in self.capabilities}

    def spend(self, amount: float) -> None:
        """Spend kinetic energy (gamma). Costs transfer to eta."""
        if amount < 0:
            raise ValueError("Cannot spend negative energy")
        # Spending moves energy from gamma to eta
        transfer(self.budget, from_gamma=True, amount=amount)
        self.tick()

    def recharge(self, amount: float) -> None:
        """Recharge kinetic energy by moving from eta to gamma."""
        if amount < 0:
            raise ValueError("Cannot recharge negative energy")
        transfer(self.budget, from_gamma=False, amount=amount)
        self.tick()

    def audit_report(self):
        return audit(self.budget)

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "state": self.state.name,
            "gamma": self.budget.gamma,
            "eta": self.budget.eta,
            "total": self.budget.total,
            "capabilities": list(self.capability_names()),
            "gamma_ratio": self.gamma_ratio,
        }
