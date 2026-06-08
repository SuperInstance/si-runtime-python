"""Tests for cellular automata grid."""

import pytest
from si_runtime.cell import Cell, Grid, new_grid


class TestCell:
    def test_default(self):
        c = Cell()
        assert c.state == 0.0
        assert c.neighbors == []


class TestGrid:
    def test_step_diffusion(self):
        """A simple diffusion rule: new state = average of neighbors."""
        def diffuse(state, neighbors):
            if not neighbors:
                return state
            return sum(neighbors) / len(neighbors)

        cells = [
            Cell(state=1.0, neighbors=[1]),
            Cell(state=0.0, neighbors=[0]),
        ]
        grid = Grid(cells, diffuse)
        grid.step()
        assert abs(cells[0].state - 0.0) < 1e-9
        assert abs(cells[1].state - 1.0) < 1e-9

    def test_run_history(self):
        def identity(state, neighbors):
            return state

        grid = new_grid(3, identity, initial=1.0)
        history = grid.run(5)
        assert len(history) == 5
        assert all(abs(h - 3.0) < 1e-9 for h in history)

    def test_new_grid_ring(self):
        grid = new_grid(4, lambda s, n: s, connectivity=1)
        for cell in grid.cells:
            assert len(cell.neighbors) == 2  # ring: left + right
