# si-runtime-python

**Pure Python runtime for the SuperInstance ecosystem.** Conservation budgets, spectral ranking, capability discovery, cellular automata, agent homeostasis, and fleet orchestration — with zero external dependencies beyond Python 3.10+.

---

## Installation

```bash
git clone https://github.com/SuperInstance/si-runtime-python.git
cd si-runtime-python
pip install -e .

# Or just add to PYTHONPATH
export PYTHONPATH=/path/to/si-runtime-python:$PYTHONPATH
```

### Requirements

- Python 3.10+ (uses `dict[str, ...]` type hints)
- `pytest` for running tests

---

## Quick Start

```python
from si_runtime import (
    Budget, AgentBudget, transfer, audit,
    adjacency_matrix, power_iteration, spectral_rank,
    Capability, Registry,
    Cell, Grid,
    Agent,
    Fleet,
)

# 1. Conservation budget
budget = Budget(total=1000.0, gamma=600.0, eta=400.0)
from si_runtime.conservation import validate_budget
print(validate_budget(budget))  # True

# 2. Agent with budget
agent = AgentBudget(id="worker-1", budget=budget)
agent.allocate(500.0)
agent.spend(200.0)
print(agent.remaining)  # 300.0

# 3. Spectral ranking
adj = adjacency_matrix(4, [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0)])
ranking = spectral_rank(adj)
print(ranking)  # [1, 2, 0, 3] — interior nodes rank highest

# 4. Capability resolution
registry = Registry()
registry.register(Capability("http", "1.0", provides=["network", "http"]))
registry.register(Capability("cache", "2.0", provides=["storage"], requires=["network"]))
results = registry.resolve(["network", "storage"])
print([c.name for c in results])  # ['http', 'cache']

# 5. Fleet orchestration
fleet = Fleet()
fleet.add_agent(Agent(id="planner"))
fleet.add_agent(Agent(id="worker"))
print(fleet.health_report())
```

---

## API Reference

### Conservation — `si_runtime.conservation`

#### `Budget`

```python
@dataclass
class Budget:
    total: float   # Total budget envelope
    gamma: float   # Spectral/productive budget
    eta: float     # Capability/entropy budget
```

#### `AgentBudget`

```python
@dataclass
class AgentBudget:
    id: str
    budget: Budget

    def allocate(self, amount: float) -> None:
        """Reserve budget. Raises ValueError if exceeds total."""

    def spend(self, amount: float) -> None:
        """Spend from allocation. Raises ValueError if exceeds allocation."""

    @property
    def remaining(self) -> float:
        """Unspent allocated budget."""
```

#### `Violation`

```python
@dataclass
class Violation:
    agent_id: str
    expected: float
    actual: float
    delta: float
```

#### Functions

```python
def validate_budget(b: Budget) -> bool:
    """Check gamma + eta == total (tolerance 1e-9)."""

def transfer(from_agent: AgentBudget, to_agent: AgentBudget, amount: float) -> None:
    """Move budget between agents, validating conservation."""

def audit(budgets: list[AgentBudget]) -> list[Violation]:
    """Audit all agent budgets for conservation violations."""
```

**Examples:**

```python
from si_runtime.conservation import Budget, AgentBudget, validate_budget, transfer, audit

# Valid budget
b = Budget(total=100.0, gamma=60.0, eta=40.0)
assert validate_budget(b) is True

# Invalid budget
bad = Budget(total=100.0, gamma=50.0, eta=30.0)
assert validate_budget(bad) is False

# Agent budget lifecycle
agent = AgentBudget(id="a1", budget=Budget(total=100.0, gamma=60.0, eta=40.0))
agent.allocate(80.0)
agent.spend(30.0)
assert agent.remaining == 50.0

# Error cases
agent.allocate(200.0)   # ValueError: exceeds budget
agent.spend(200.0)      # ValueError: exceeds allocation
agent.allocate(-5.0)    # ValueError: negative amount

# Transfer between agents
a1 = AgentBudget(id="a1", budget=Budget(total=100.0, gamma=60.0, eta=40.0))
a2 = AgentBudget(id="a2", budget=Budget(total=100.0, gamma=60.0, eta=40.0))
a1.allocate(50.0)
transfer(a1, a2, 20.0)
assert a1.remaining == 30.0
assert a2.remaining == 20.0

# Fleet audit
agents = [
    AgentBudget(id="ok", budget=Budget(total=10.0, gamma=6.0, eta=4.0)),
    AgentBudget(id="bad", budget=Budget(total=10.0, gamma=3.0, eta=3.0)),
]
violations = audit(agents)
assert len(violations) == 1
assert violations[0].agent_id == "bad"
```

---

### Spectral — `si_runtime.spectral`

```python
def adjacency_matrix(n: int, edges: list[tuple[int, int, float]]) -> list[list[float]]:
    """Build an n×n symmetric adjacency matrix from edges."""

def power_iteration(matrix: list[list[float]], iterations: int = 100) -> list[float]:
    """Compute dominant eigenvector via power iteration."""

def spectral_rank(adj_matrix: list[list[float]]) -> list[int]:
    """Return node indices ranked by eigenvector centrality (descending)."""
```

**Examples:**

```python
from si_runtime.spectral import adjacency_matrix, power_iteration, spectral_rank

# Build a 4-node line graph: 0-1-2-3
adj = adjacency_matrix(4, [
    (0, 1, 1.0),
    (1, 2, 1.0),
    (2, 3, 1.0),
])

# Get eigenvector
ev = power_iteration(adj, iterations=200)
print([f"{v:.4f}" for v in ev])
# Interior nodes have higher values

# Rank by centrality
ranking = spectral_rank(adj)
print(ranking)  # [1, 2, 0, 3] — interior nodes first

# Complete graph (all equal centrality)
complete = adjacency_matrix(3, [(0, 1, 1.0), (1, 2, 1.0), (0, 2, 1.0)])
ranking = spectral_rank(complete)
# All nodes have similar centrality

# Star graph (center is most central)
star = adjacency_matrix(4, [(0, 1, 1.0), (0, 2, 1.0), (0, 3, 1.0)])
ranking = spectral_rank(star)
assert ranking[0] == 0  # Center node ranks first

# Empty graph
empty = adjacency_matrix(0, [])
assert power_iteration(empty) == []
```

---

### Capability — `si_runtime.capability`

#### `Capability`

```python
@dataclass
class Capability:
    name: str
    version: str
    provides: list[str] = field(default_factory=list)
    requires: list[str] = field(default_factory=list)
```

#### `Registry`

```python
class Registry:
    def register(self, cap: Capability) -> None:
        """Register a capability."""

    def match(self, required: str) -> list[Capability]:
        """Find capabilities whose provides include `required`."""

    def resolve(self, needs: list[str]) -> list[Capability]:
        """Resolve needs to a minimal capability set (greedy)."""
```

**Examples:**

```python
from si_runtime.capability import Capability, Registry

registry = Registry()
registry.register(Capability("http", "1.0", provides=["network", "http"]))
registry.register(Capability("grpc", "1.0", provides=["network", "rpc"]))
registry.register(Capability("cache", "2.0", provides=["storage"], requires=["network"]))

# Find providers of "network"
providers = registry.match("network")
assert len(providers) == 2
print([c.name for c in providers])  # ['http', 'grpc']

# Resolve a task's needs
resolved = registry.resolve(["network", "storage"])
print([c.name for c in resolved])  # ['http', 'cache']

# Unresolvable need
resolved = registry.resolve(["quantum-computing"])
print(len(resolved))  # 0
```

---

### Cell — `si_runtime.cell`

#### `Cell`

```python
@dataclass
class Cell:
    state: float = 0.0
    neighbors: list[int] = field(default_factory=list)
```

#### `Grid`

```python
class Grid:
    def __init__(self, cells: list[Cell], rule: Rule) -> None: ...

    def step(self) -> None:
        """Advance one time step."""

    def run(self, n_steps: int) -> list[float]:
        """Run n_steps, returning total-state history."""
```

#### `new_grid()`

```python
def new_grid(size: int, rule: Rule, initial: float = 0.0, connectivity: int = 1) -> Grid:
    """Create a 1-D ring grid with given connectivity radius."""
```

**Rule type:** `Callable[[float, list[float]], float]` — takes a cell's state and its neighbors' states, returns the new state.

**Examples:**

```python
from si_runtime.cell import Cell, Grid, new_grid

# Averaging rule: each cell moves toward its neighbors' mean
def average_rule(state: float, neighbors: list[float]) -> float:
    if not neighbors:
        return state
    return (state + sum(neighbors)) / (1 + len(neighbors))

# Create a 10-cell ring grid
grid = new_grid(10, average_rule, initial=0.0, connectivity=1)

# Set one cell to a high value
grid.cells[0].state = 100.0

# Run for 50 steps — watch the value diffuse
history = grid.run(50)
print(f"Initial total: {history[0]:.2f}")
print(f"Final total: {history[-1]:.2f}")

# Custom 2-cell grid
cells = [Cell(state=0.0), Cell(state=10.0)]
cells[0].neighbors = [1]
cells[1].neighbors = [0]

def midpoint_rule(state: float, neighbors: list[float]) -> float:
    return sum(neighbors) / len(neighbors)

grid = Grid(cells, midpoint_rule)
grid.run(20)
# Both cells converge to 5.0
print([f"{c.state:.2f}" for c in grid.cells])
```

---

### Agent — `si_runtime.agent`

```python
@dataclass
class Agent:
    id: str
    state: dict[str, Any] = field(default_factory=dict)
    capabilities: list[Capability] = field(default_factory=list)
    gauges: dict[str, float] = field(default_factory=dict)

    def add_gauge(self, name: str, value: float) -> None:
        """Add a homeostatic gauge."""

    def homeostasis(self, targets: dict[str, float], dt: float = 1.0) -> None:
        """PID regulation: drive gauges toward targets."""
```

**Examples:**

```python
from si_runtime.agent import Agent

# Create an agent with gauges
agent = Agent(id="worker-1")
agent.add_gauge("cpu", 0.8)
agent.add_gauge("memory", 0.6)
agent.add_gauge("temperature", 72.0)

# Set targets and regulate
agent.homeostasis({"cpu": 0.5, "memory": 0.4, "temperature": 65.0})
print(agent.gauges)
# Values move toward targets via PID control

# Multiple regulation steps
for _ in range(20):
    agent.homeostasis({"temperature": 65.0})
print(f"Temperature: {agent.gauges['temperature']:.2f}")
# Converges toward 65.0
```

---

### Fleet — `si_runtime.fleet`

```python
@dataclass
class Fleet:
    agents: list[Agent] = field(default_factory=list)
    adjacency: list[list[float]] = field(default_factory=list)

    def add_agent(self, agent: Agent, budget: AgentBudget | None = None) -> None:
        """Add an agent with optional budget."""

    def spectral_rank(self) -> list[int]:
        """Rank agents by eigenvector centrality."""

    def conservation_audit(self) -> list[Violation]:
        """Check all tracked budgets for conservation violations."""

    def health_report(self) -> dict:
        """Fleet-wide health summary."""
```

**Examples:**

```python
from si_runtime.fleet import Fleet
from si_runtime.agent import Agent
from si_runtime.conservation import Budget, AgentBudget

# Build a fleet with agents and budgets
fleet = Fleet()
fleet.add_agent(
    Agent(id="planner"),
    AgentBudget(id="planner", budget=Budget(total=100.0, gamma=60.0, eta=40.0)),
)
fleet.add_agent(
    Agent(id="executor"),
    AgentBudget(id="executor", budget=Budget(total=200.0, gamma=120.0, eta=80.0)),
)

# Fleet health
report = fleet.health_report()
print(report)
# {
#   'agent_count': 2,
#   'spectral_ranking': [0, 1],
#   'conservation_violations': 0,
#   'total_gauges': 0
# }

# Spectral ranking with adjacency matrix
fleet.adjacency = [
    [0.0, 1.0, 0.0, 0.0],
    [1.0, 0.0, 1.0, 0.0],
    [0.0, 1.0, 0.0, 1.0],
    [0.0, 0.0, 1.0, 0.0],
]
for i in range(4):
    fleet.add_agent(Agent(id=f"n{i}"))
ranking = fleet.spectral_rank()
# Interior nodes (1, 2) rank before leaf nodes (0, 3)

# Conservation audit with violations
fleet2 = Fleet()
fleet2.add_agent(
    Agent(id="ok"),
    AgentBudget(id="ok", budget=Budget(total=10.0, gamma=6.0, eta=4.0)),
)
fleet2.add_agent(
    Agent(id="bad"),
    AgentBudget(id="bad", budget=Budget(total=10.0, gamma=3.0, eta=3.0)),
)
violations = fleet2.conservation_audit()
assert len(violations) == 1
assert violations[0].agent_id == "bad"
```

---

## Supabase Integration

Use `si-runtime-python` to interact with the Supabase fleet registry:

```python
#!/usr/bin/env python3
"""Sync fleet state to Supabase."""

import os
from supabase import create_client  # pip install supabase
from si_runtime import Fleet, Agent, Budget, AgentBudget

# Build fleet
fleet = Fleet()
fleet.add_agent(
    Agent(id="agent-alpha"),
    AgentBudget(id="agent-alpha", budget=Budget(total=225.0, gamma=143.0, eta=82.0)),
)
fleet.add_agent(
    Agent(id="agent-beta"),
    AgentBudget(id="agent-beta", budget=Budget(total=100.0, gamma=60.0, eta=40.0)),
)

# Push budgets to Supabase
url = os.environ["SUPABASE_URL"]
key = os.environ["SUPABASE_SERVICE_KEY"]
supabase = create_client(url, key)

for agent in fleet.agents:
    budget = fleet._budgets[0].budget  # simplified
    supabase.table("fleet_budgets").upsert({
        "agent_id": agent.id,
        "total_budget": budget.total,
        "gamma": budget.gamma,
        "eta": budget.eta,
    }).execute()
```

---

## Working Examples

### Full Fleet Simulation

```python
#!/usr/bin/env python3
"""Simulate a fleet of agents with conservation and spectral ranking."""

from si_runtime import (
    Fleet, Agent, Budget, AgentBudget,
    adjacency_matrix, spectral_rank,
)
from si_runtime.conservation import audit

# Create agents
agents = []
budgets = []
for i in range(5):
    gamma = 100 - i * 10
    eta = 50 - i * 5
    agent = Agent(id=f"agent-{i}")
    ab = AgentBudget(
        id=f"agent-{i}",
        budget=Budget(total=gamma + eta, gamma=gamma, eta=eta),
    )
    agents.append(agent)
    budgets.append(ab)

# Build fleet with interaction graph
fleet = Fleet()
fleet.adjacency = adjacency_matrix(5, [
    (0, 1, 0.9), (1, 2, 0.7), (2, 3, 0.8), (3, 4, 0.6),
    (0, 2, 0.3), (1, 3, 0.4),
])
for agent, budget in zip(agents, budgets):
    fleet.add_agent(agent, budget)

# Audit conservation
violations = fleet.conservation_audit()
print(f"Conservation violations: {len(violations)}")

# Spectral ranking
ranking = fleet.spectral_rank()
print(f"Spectral ranking: {ranking}")

# Health report
report = fleet.health_report()
print(f"Health: {report}")
```

### Cellular Automata Simulation

```python
#!/usr/bin/env python3
"""Diffusion simulation using the cellular automata grid."""

from si_runtime.cell import new_grid

# Diffusion rule: cell moves toward neighbor average
def diffusion(state, neighbors):
    if not neighbors:
        return state
    avg = sum(neighbors) / len(neighbors)
    return state + 0.3 * (avg - state)  # diffusion rate of 0.3

# 20-cell ring with 2-neighbor connectivity
grid = new_grid(20, diffusion, initial=0.0, connectivity=2)

# Heat source at center
grid.cells[10].state = 100.0

# Simulate diffusion
history = grid.run(100)
print(f"Step 0: total = {history[0]:.2f}")
print(f"Step 50: total = {history[50]:.2f}")
print(f"Step 99: total = {history[99]:.2f}")

# Check that total is conserved (heat doesn't disappear)
assert abs(history[0] - history[-1]) < 1e-10
```

---

## Architecture

```
si_runtime/
├── __init__.py        # Public API exports
├── conservation.py    # Budget, AgentBudget, Violation, transfer, audit
├── spectral.py        # adjacency_matrix, power_iteration, spectral_rank
├── capability.py      # Capability, Registry
├── cell.py            # Cell, Grid, new_grid
├── agent.py           # Agent with PID homeostasis
└── fleet.py           # Fleet orchestration

tests/
├── test_conservation.py
├── test_spectral.py
├── test_capability.py
├── test_cell.py
├── test_agent.py
└── test_fleet.py
```

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

```
tests/test_conservation.py::TestBudget::test_valid_budget PASSED
tests/test_conservation.py::TestBudget::test_invalid_budget PASSED
tests/test_conservation.py::TestAgentBudget::test_allocate_and_remaining PASSED
tests/test_conservation.py::TestTransfer::test_transfer_success PASSED
tests/test_conservation.py::TestTransfer::test_transfer_insufficient PASSED
tests/test_conservation.py::TestAudit::test_audit_clean PASSED
tests/test_conservation.py::TestAudit::test_audit_violation PASSED
tests/test_fleet.py::TestFleet::test_add_agent PASSED
tests/test_fleet.py::TestFleet::test_spectral_rank_with_adjacency PASSED
tests/test_fleet.py::TestFleet::test_conservation_audit PASSED
tests/test_fleet.py::TestFleet::test_health_report PASSED
```

---

## Related Repos

| Repo | Language | Description |
|------|----------|-------------|
| [`conservation-law`](https://github.com/SuperInstance/conservation-law) | Rust | Core conservation law crate |
| [`si-conservation-python`](https://github.com/SuperInstance/si-conservation-python) | Rust/Python | PyO3 bindings (faster for heavy compute) |
| [`si-runtime-go`](https://github.com/SuperInstance/si-runtime-go) | Go | Go runtime with same API |
| [`si-cli`](https://github.com/SuperInstance/si-cli) | Rust | CLI for fleet management |
| [`si-fleet-api`](https://github.com/SuperInstance/si-fleet-api) | TypeScript | REST API for fleet budgets |

---

## License

MIT
