"""Fleet orchestration — manage multiple agents with spectral ranking and conservation auditing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .agent import Agent
from .conservation import Audit, audit
from .spectral import AdjacencyMatrix, spectral_rank


@dataclass
class Fleet:
    """A fleet of agents with orchestration, ranking, and conservation auditing."""

    name: str = "default"
    _agents: Dict[str, Agent] = field(default_factory=dict, repr=False)
    _interaction_matrix: Optional[AdjacencyMatrix] = None

    def add_agent(self, agent: Agent) -> None:
        if agent.agent_id in self._agents:
            raise ValueError(f"Agent {agent.agent_id} already in fleet")
        self._agents[agent.agent_id] = agent
        self._interaction_matrix = None  # invalidate cache

    def remove_agent(self, agent_id: str) -> Optional[Agent]:
        agent = self._agents.pop(agent_id, None)
        if agent:
            self._interaction_matrix = None
        return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self._agents.get(agent_id)

    @property
    def agent_ids(self) -> List[str]:
        return list(self._agents.keys())

    @property
    def size(self) -> int:
        return len(self._agents)

    def agents(self) -> List[Agent]:
        return list(self._agents.values())

    def spectral_rank(self) -> List[Tuple[str, float]]:
        """Rank agents by eigenvalue centrality in the interaction graph.

        Builds an adjacency matrix from agent interactions (shared capabilities)
        and runs power iteration to find the most central agents.
        """
        ids = self.agent_ids
        n = len(ids)
        if n == 0:
            return []
        if n == 1:
            return [(ids[0], 1.0)]

        # Build adjacency: weight = number of shared capabilities / max possible
        matrix = [[0.0] * n for _ in range(n)]
        agents = self.agents()
        for i in range(n):
            caps_i = agents[i].capability_names()
            for j in range(n):
                if i == j:
                    matrix[i][j] = float(len(caps_i))
                    continue
                caps_j = agents[j].capability_names()
                shared = len(caps_i & caps_j)
                total = max(1, len(caps_i | caps_j))
                matrix[i][j] = shared / total

        adj = AdjacencyMatrix(matrix)
        rankings = spectral_rank(adj)
        return [(ids[idx], ev) for idx, ev in rankings]

    def conservation_audit(self) -> Dict[str, Audit]:
        """Run conservation audits on every agent in the fleet."""
        return {
            agent_id: audit(agent.budget)
            for agent_id, agent in self._agents.items()
        }

    def fleet_health(self) -> dict:
        """Aggregate health metrics across the fleet."""
        audits = self.conservation_audit()
        if not audits:
            return {"status": "empty", "agents": 0}

        valid_count = sum(1 for a in audits.values() if a.valid)
        total_gamma = sum(a.gamma for a in audits.values())
        total_eta = sum(a.eta for a in audits.values())
        total_budget = sum(a.total for a in audits.values())

        stressed = [
            aid for aid, agent in self._agents.items()
            if agent.state.name == "STRESSED"
        ]

        return {
            "status": "healthy" if not stressed else "degraded",
            "agents": len(audits),
            "valid_budgets": valid_count,
            "total_gamma": total_gamma,
            "total_eta": total_eta,
            "total_budget": total_budget,
            "stressed_agents": stressed,
        }

    def broadcast(self, action: callable) -> None:
        """Run an action on every agent."""
        for agent in self._agents.values():
            action(agent)

    def __len__(self) -> int:
        return len(self._agents)

    def __iter__(self):
        return iter(self._agents.values())

    def __contains__(self, agent_id: str) -> bool:
        return agent_id in self._agents
