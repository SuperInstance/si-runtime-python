"""Cellular automata grid with pluggable rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


Rule = Callable[[float, list[float]], float]


@dataclass
class Cell:
    """A single cell with float state and neighbor indices."""
    state: float = 0.0
    neighbors: list[int] = field(default_factory=list)


class Grid:
    """A grid of cells that evolve according to a rule function."""

    def __init__(self, cells: list[Cell], rule: Rule) -> None:
        self.cells = cells
        self.rule = rule
        self._history: list[float] = []

    def step(self) -> None:
        """Advance one time step."""
        neighbor_states = [
            [self.cells[j].state for j in c.neighbors]
            for c in self.cells
        ]
        for i, cell in enumerate(self.cells):
            cell.state = self.rule(cell.state, neighbor_states[i])
        self._history.append(sum(c.state for c in self.cells))

    def run(self, n_steps: int) -> list[float]:
        """Run for n_steps, returning the total-state history."""
        self._history.clear()
        for _ in range(n_steps):
            self.step()
        return list(self._history)


def new_grid(size: int, rule: Rule, initial: float = 0.0, connectivity: int = 1) -> Grid:
    """Factory: create a 1-D ring grid with given connectivity radius."""
    cells = [Cell(state=initial) for _ in range(size)]
    for i in range(size):
        for d in range(1, connectivity + 1):
            cells[i].neighbors.append((i - d) % size)
            cells[i].neighbors.append((i + d) % size)
    return Grid(cells, rule)
