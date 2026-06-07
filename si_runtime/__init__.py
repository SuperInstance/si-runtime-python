"""SuperInstance Python Runtime — unified runtime for constraint-aware AI."""

__version__ = "0.1.0"

from .conservation import Budget, AgentBudget, allocate, transfer, audit
from .spectral import AdjacencyMatrix, power_iteration, spectral_rank
from .capability import Capability, Registry, match_capabilities
from .cell import Cell
from .agent import Agent
from .fleet import Fleet

__all__ = [
    "Budget",
    "AgentBudget",
    "allocate",
    "transfer",
    "audit",
    "AdjacencyMatrix",
    "power_iteration",
    "spectral_rank",
    "Capability",
    "Registry",
    "match_capabilities",
    "Cell",
    "Agent",
    "Fleet",
]
