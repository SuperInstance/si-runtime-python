"""Capability registry and matching for agent ecosystems."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


@dataclass(frozen=True)
class Capability:
    """A named capability with optional tags and version."""
    name: str
    tags: Tuple[str, ...] = ()
    version: str = "1.0.0"
    description: str = ""

    def matches(self, other: "Capability") -> bool:
        """True if this capability satisfies the other (same name, compatible tags)."""
        if self.name != other.name:
            return False
        # All required tags of other must be present in self
        return all(tag in self.tags for tag in other.tags)


class Registry:
    """Central registry of capabilities offered by agents or services."""

    def __init__(self):
        self._caps: Dict[str, Capability] = {}
        self._owners: Dict[str, Set[str]] = {}  # cap_name -> {owner_id}

    def register(self, cap: Capability, owner_id: str) -> None:
        """Register a capability under an owner."""
        self._caps[cap.name] = cap
        self._owners.setdefault(cap.name, set()).add(owner_id)

    def unregister(self, cap_name: str, owner_id: str) -> bool:
        """Remove a capability from an owner. Returns True if removed."""
        owners = self._owners.get(cap_name)
        if owners and owner_id in owners:
            owners.discard(owner_id)
            if not owners:
                self._caps.pop(cap_name, None)
                self._owners.pop(cap_name, None)
            return True
        return False

    def get(self, name: str) -> Optional[Capability]:
        return self._caps.get(name)

    def owners(self, cap_name: str) -> Set[str]:
        return set(self._owners.get(cap_name, set()))

    def all_capabilities(self) -> List[Capability]:
        return list(self._caps.values())

    def __len__(self) -> int:
        return len(self._caps)

    def __contains__(self, name: str) -> bool:
        return name in self._caps


def match_capabilities(
    required: List[Capability],
    offered: List[Capability],
) -> Tuple[List[Capability], List[Capability]]:
    """Match required capabilities against offered ones.

    Returns (matched, unmatched).
    """
    matched = []
    unmatched = []
    offered_by_name: Dict[str, List[Capability]] = {}
    for cap in offered:
        offered_by_name.setdefault(cap.name, []).append(cap)

    for req in required:
        candidates = offered_by_name.get(req.name, [])
        found = False
        for cand in candidates:
            if cand.matches(req):
                matched.append(req)
                found = True
                break
        if not found:
            unmatched.append(req)

    return matched, unmatched
