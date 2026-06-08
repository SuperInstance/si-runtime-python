"""Tests for capability discovery and resolution."""

import pytest
from si_runtime.capability import Capability, Registry


class TestCapability:
    def test_creation(self):
        c = Capability(name="http", version="1.0", provides=["network"], requires=[])
        assert c.name == "http"


class TestRegistry:
    @pytest.fixture
    def registry(self):
        r = Registry()
        r.register(Capability("http", "1.0", provides=["network", "http"], requires=[]))
        r.register(Capability("grpc", "1.0", provides=["network", "rpc"], requires=[]))
        r.register(Capability("cache", "2.0", provides=["storage"], requires=["network"]))
        return r

    def test_match(self, registry):
        results = registry.match("network")
        assert len(results) == 2
        names = {c.name for c in results}
        assert names == {"http", "grpc"}

    def test_match_empty(self, registry):
        assert registry.match("nonexistent") == []

    def test_resolve_single(self, registry):
        resolved = registry.resolve(["http"])
        assert len(resolved) == 1
        assert resolved[0].name == "http"

    def test_resolve_multiple(self, registry):
        resolved = registry.resolve(["network", "storage"])
        assert len(resolved) == 2
