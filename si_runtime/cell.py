"""Cellular automaton — local update rules with neighbor coupling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple


State = float
UpdateRule = Callable[["Cell", List["Cell"]], State]


@dataclass
class Cell:
    """A cell in an automaton with local state and neighbor coupling.

    Each cell carries a conservation budget. Updates cost energy.
    """
    name: str
    state: State = 0.0
    energy_cost: float = 0.01
    _neighbors: List["Cell"] = field(default_factory=list, repr=False)
    _history: List[State] = field(default_factory=list, repr=False)

    def add_neighbor(self, other: "Cell", bidirectional: bool = True) -> None:
        if other not in self._neighbors:
            self._neighbors.append(other)
        if bidirectional:
            if self not in other._neighbors:
                other._neighbors.append(self)

    def remove_neighbor(self, other: "Cell", bidirectional: bool = True) -> None:
        if other in self._neighbors:
            self._neighbors.remove(other)
        if bidirectional:
            if self in other._neighbors:
                other._neighbors.remove(self)

    @property
    def neighbors(self) -> List["Cell"]:
        return list(self._neighbors)

    @property
    def degree(self) -> int:
        return len(self._neighbors)

    def update(self, rule: UpdateRule) -> State:
        """Apply update rule and record history."""
        new_state = rule(self, self._neighbors)
        self._history.append(self.state)
        self.state = new_state
        return new_state

    def mean_field(self) -> float:
        """Average state of neighbors."""
        if not self._neighbors:
            return 0.0
        return sum(n.state for n in self._neighbors) / len(self._neighbors)

    @property
    def history(self) -> List[float]:
        return list(self._history)

    def energy_spent(self) -> float:
        """Total energy spent = updates * energy_cost."""
        return len(self._history) * self.energy_cost

    def __hash__(self) -> int:
        return id(self)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Cell):
            return NotImplemented
        return self is other
