"""Tests for spectral ranking."""

import pytest
import math
from si_runtime.spectral import adjacency_matrix, power_iteration, spectral_rank


class TestAdjacencyMatrix:
    @pytest.mark.parametrize("n,edges,expected_nonzero", [
        (3, [(0, 1, 1.0), (1, 2, 2.0)], 4),
        (2, [(0, 1, 0.5)], 2),
        (4, [], 0),
    ])
    def test_matrix_shape_and_nonzero(self, n, edges, expected_nonzero):
        mat = adjacency_matrix(n, edges)
        assert len(mat) == n
        assert all(len(row) == n for row in mat)
        nonzero = sum(1 for row in mat for v in row if v != 0.0)
        assert nonzero == expected_nonzero

    def test_out_of_bounds_edge(self):
        with pytest.raises(IndexError):
            adjacency_matrix(2, [(0, 5, 1.0)])


class TestPowerIteration:
    def test_converges(self):
        mat = adjacency_matrix(3, [(0, 1, 1.0), (1, 2, 1.0)])
        ev = power_iteration(mat, iterations=200)
        assert len(ev) == 3
        # Eigenvector should be normalized
        norm = math.sqrt(sum(x * x for x in ev))
        assert abs(norm - 1.0) < 1e-6

    def test_empty_matrix(self):
        assert power_iteration([], 10) == []


class TestSpectralRank:
    def test_star_graph(self):
        """Node 0 is the hub of a 5-node star — should rank first."""
        edges = [(0, i, 1.0) for i in range(1, 5)]
        mat = adjacency_matrix(5, edges)
        rank = spectral_rank(mat)
        assert rank[0] == 0  # hub is most central

    def test_single_node(self):
        assert spectral_rank([[1.0]]) == [0]
