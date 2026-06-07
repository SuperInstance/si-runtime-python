"""Spectral analysis — power iteration for ranking and eigenvalue extraction."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class AdjacencyMatrix:
    """Immutable square adjacency matrix backed by a list of lists."""
    data: List[List[float]]

    def __post_init__(self):
        n = len(self.data)
        if n == 0:
            raise ValueError("Matrix must be non-empty")
        for row in self.data:
            if len(row) != n:
                raise ValueError("Matrix must be square")

    @property
    def size(self) -> int:
        return len(self.data)

    def row(self, i: int) -> List[float]:
        return self.data[i]

    def __matmul__(self, vec: List[float]) -> List[float]:
        """Matrix-vector multiplication."""
        n = self.size
        result = [0.0] * n
        for i in range(n):
            s = 0.0
            row = self.data[i]
            for j in range(n):
                s += row[j] * vec[j]
            result[i] = s
        return result


def _normalize(vec: List[float]) -> float:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm > 1e-12:
        for i in range(len(vec)):
            vec[i] /= norm
    return norm


def power_iteration(
    matrix: AdjacencyMatrix,
    iterations: int = 200,
    seed: Optional[int] = None,
) -> Tuple[float, List[float]]:
    """Return the dominant eigenvalue and eigenvector via power iteration."""
    n = matrix.size

    # Deterministic initial vector based on seed
    import random
    rng = random.Random(seed if seed is not None else 42)
    vec = [rng.random() for _ in range(n)]
    _normalize(vec)

    eigenvalue = 0.0
    buf = [0.0] * n
    mu = [0.0, 0.0]

    for _ in range(iterations):
        buf = matrix @ vec

        # Rayleigh quotient
        eigenvalue = sum(v * b for v, b in zip(vec, buf))

        _normalize(buf)
        vec, buf = buf, vec

        # Convergence check
        new_mu = eigenvalue
        if abs(new_mu - mu[1]) < 1e-10 and abs(mu[1] - mu[0]) < 1e-10:
            break
        mu[0] = mu[1]
        mu[1] = new_mu

    return eigenvalue, vec


def spectral_rank(
    matrix: AdjacencyMatrix,
    iterations: int = 200,
) -> List[Tuple[int, float]]:
    """Rank nodes by eigenvalue magnitude using deflation power iteration.

    Returns a list of (node_index, eigenvalue) sorted by eigenvalue descending.
    """
    n = matrix.size
    # Deep copy matrix data for deflation
    residual = [row[:] for row in matrix.data]
    rankings: List[Tuple[int, float]] = []
    used = [False] * n

    buf = [0.0] * n

    for k in range(n):
        # Initialize vector
        vec = [math.sin((j + k * 7 + 1) * 1.23456) for j in range(n)]
        _normalize(vec)

        eigenvalue = 0.0
        mu = [0.0, 0.0]

        for _ in range(iterations):
            # matvec with residual
            for i in range(n):
                s = 0.0
                for j in range(n):
                    s += residual[i][j] * vec[j]
                buf[i] = s

            eigenvalue = sum(v * b for v, b in zip(vec, buf))
            _normalize(buf)
            vec, buf = buf, vec

            new_mu = eigenvalue
            if abs(new_mu - mu[1]) < 1e-10 and abs(mu[1] - mu[0]) < 1e-10:
                break
            mu[0] = mu[1]
            mu[1] = new_mu

        # Find best unused node
        best_idx = max(
            (i for i in range(n) if not used[i]),
            key=lambda i: abs(vec[i]),
            default=-1,
        )
        if best_idx >= 0:
            used[best_idx] = True
            rankings.append((best_idx, eigenvalue))

        # Deflate: R = R - lambda * v * v^T
        for i in range(n):
            for j in range(n):
                residual[i][j] -= eigenvalue * vec[i] * vec[j]

    # Sort by eigenvalue magnitude descending
    rankings.sort(key=lambda x: abs(x[1]), reverse=True)
    return rankings
