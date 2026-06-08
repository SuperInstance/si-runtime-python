"""Capability discovery and resolution."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Capability:
    """Describes a named capability with version, provides, and requires."""
    name: str
    version: str
    provides: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)


class Registry:
    """Register capabilities and resolve dependency chains."""

    def __init__(self) -> None:
        self._caps: dict[str, Capability] = {}

    def register(self, cap: Capability) -> None:
        self._caps[cap.name] = cap

    def match(self, required: str) -> list[Capability]:
        """Find all capabilities whose `provides` includes `required`."""
        return [
            c for c in self._caps.values() if required in c.provides
        ]

    def resolve(self, needs: list[str]) -> list[Capability]:
        """Resolve a list of needs to a minimal set of capabilities.

        Greedy approach: for each need, pick the first matching capability.
        """
        resolved: list[Capability] = []
        seen: set[str] = set()
        for need in needs:
            for c in self._caps.values():
                if need in c.provides and c.name not in seen:
                    resolved.append(c)
                    seen.add(c.name)
                    break
        return resolved
