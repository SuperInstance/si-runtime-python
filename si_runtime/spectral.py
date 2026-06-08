"""Spectral ranking via power iteration on adjacency graphs."""

from __future__ import annotations

import math


def adjacency_matrix(n: int, edges: list[tuple[int, int, float]]) -> list[list[float]]:
    """Build an n×n adjacency matrix from a list of (i, j, weight) edges."""
    mat = [[0.0] * n for _ in range(n)]
    for i, j, w in edges:
        if i < 0 or i >= n or j < 0 or j >= n:
            raise IndexError(f"edge ({i}, {j}) out of bounds for matrix of size {n}")
        mat[i][j] += w
        mat[j][i] += w  # undirected
    return mat


def power_iteration(matrix: list[list[float]], iterations: int = 100) -> list[float]:
    """Compute the dominant eigenvector via power iteration."""
    n = len(matrix)
    if n == 0:
        return []
    vec = [1.0 / n] * n
    for _ in range(iterations):
        new_vec = [0.0] * n
        for i in range(n):
            for j in range(n):
                new_vec[i] += matrix[i][j] * vec[j]
        norm = math.sqrt(sum(x * x for x in new_vec))
        if norm < 1e-15:
            return vec
        vec = [x / norm for x in new_vec]
    return vec


def spectral_rank(adj_matrix: list[list[float]]) -> list[int]:
    """Return node indices ranked by eigenvector centrality (descending)."""
    ev = power_iteration(adj_matrix)
    indexed = list(enumerate(ev))
    indexed.sort(key=lambda x: x[1], reverse=True)
    return [i for i, _ in indexed]
