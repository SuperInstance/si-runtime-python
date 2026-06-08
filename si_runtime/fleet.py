"""Fleet — multi-agent orchestration with spectral ranking and conservation audits."""

from __future__ import annotations

from dataclasses import dataclass, field

from .agent import Agent
from .conservation import AgentBudget, audit as conservation_audit
from .spectral import spectral_rank as _spectral_rank


@dataclass
class Fleet:
    """A fleet of agents with adjacency and budget tracking."""
    agents: list[Agent] = field(default_factory=list)
    adjacency: list[list[float]] = field(default_factory=list)
    _budgets: list[AgentBudget] = field(default_factory=list, repr=False)

    def add_agent(self, agent: Agent, budget: AgentBudget | None = None) -> None:
        self.agents.append(agent)
        if budget:
            self._budgets.append(budget)

    def spectral_rank(self) -> list[int]:
        """Rank agents by eigenvector centrality on the adjacency matrix."""
        if not self.adjacency:
            return list(range(len(self.agents)))
        return _spectral_rank(self.adjacency)

    def conservation_audit(self) -> list:
        """Run conservation audit on all tracked budgets."""
        return conservation_audit(self._budgets)

    def health_report(self) -> dict:
        """Summarize fleet health."""
        return {
            "agent_count": len(self.agents),
            "spectral_ranking": self.spectral_rank(),
            "conservation_violations": len(self.conservation_audit()),
            "total_gauges": sum(len(a.gauges) for a in self.agents),
        }
