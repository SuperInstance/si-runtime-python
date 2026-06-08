# si-runtime-python

Python runtime for the SuperInstance ecosystem. Provides conservation budgets, spectral ranking, capability discovery, cellular automata, agent homeostasis, and fleet orchestration.

## Installation

```bash
pip install si-runtime
```

Requires Python 3.10+.

## Quick Start

```python
from si_runtime import Budget, AgentBudget, transfer, audit
from si_runtime import adjacency_matrix, spectral_rank
from si_runtime import Capability, Registry
from si_runtime import Agent
from si_runtime import Fleet
```

---

## Conservation Budgets

The conservation module enforces the invariant **gamma + eta == total** across all agent budgets.

### Creating Budgets

```python
from si_runtime import Budget, AgentBudget

budget = Budget(total=100.0, gamma=60.0, eta=40.0)
agent = AgentBudget(id="worker-1", budget=budget)

agent.allocate(50.0)
print(agent.remaining)  # 50.0

agent.spend(20.0)
print(agent.remaining)  # 30.0
```

**Expected output:**
```
50.0
30.0
```

### Transferring Budget Between Agents

```python
from si_runtime import Budget, AgentBudget, transfer

b1 = Budget(total=100.0, gamma=60.0, eta=40.0)
b2 = Budget(total=100.0, gamma=60.0, eta=40.0)

alice = AgentBudget(id="alice", budget=b1)
bob = AgentBudget(id="bob", budget=b2)

alice.allocate(80.0)

transfer(alice, bob, 30.0)

print(f"Alice remaining: {alice.remaining}")  # 50.0
print(f"Bob remaining:   {bob.remaining}")    # 30.0
```

**Expected output:**
```
Alice remaining: 50.0
Bob remaining:   30.0
```

### Auditing Budgets

```python
from si_runtime import Budget, AgentBudget, audit

# Valid budget
good = AgentBudget(id="good", budget=Budget(total=10.0, gamma=6.0, eta=4.0))

# Invalid budget — gamma + eta != total
bad = AgentBudget(id="bad", budget=Budget(total=10.0, gamma=3.0, eta=3.0))

violations = audit([good, bad])
for v in violations:
    print(f"Violation: {v.agent_id} expected={v.expected} actual={v.actual} delta={v.delta}")
```

**Expected output:**
```
Violation: bad expected=10.0 actual=6.0 delta=4.0
```

---

## Spectral Ranking

Rank nodes in a graph by eigenvector centrality using power iteration.

### Building an Adjacency Matrix

```python
from si_runtime import adjacency_matrix

# 4-node ring
edges = [
    (0, 1, 1.0),
    (1, 2, 1.0),
    (2, 3, 1.0),
    (3, 0, 1.0),
]
mat = adjacency_matrix(4, edges)
for row in mat:
    print(row)
```

**Expected output:**
```
[0.0, 1.0, 0.0, 1.0]
[1.0, 0.0, 1.0, 0.0]
[0.0, 1.0, 0.0, 1.0]
[1.0, 0.0, 1.0, 0.0]
```

### Computing Eigenvector Centrality

```python
from si_runtime import adjacency_matrix, power_iteration

mat = adjacency_matrix(4, [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0), (3, 0, 1.0)])
ev = power_iteration(mat, iterations=100)
print([round(v, 4) for v in ev])
```

**Expected output:**
```
[0.5, 0.5, 0.5, 0.5]
```

### Spectral Rank on a Star Graph

```python
from si_runtime import adjacency_matrix, spectral_rank

# Star: node 0 connected to all others
edges = [(0, i, 1.0) for i in range(1, 5)]
mat = adjacency_matrix(5, edges)
rank = spectral_rank(mat)
print(f"Most central node: {rank[0]}")
print(f"Full ranking: {rank}")
```

**Expected output:**
```
Most central node: 0
Full ranking: [0, 1, 2, 3, 4]
```

---

## Capability Discovery

Register and resolve capabilities by what they provide and require.

### Basic Registration and Matching

```python
from si_runtime import Capability, Registry

registry = Registry()

registry.register(Capability(
    name="http-server",
    version="1.2.0",
    provides=["network", "http"],
    requires=[],
))

registry.register(Capability(
    name="grpc-server",
    version="0.9.0",
    provides=["network", "rpc"],
    requires=[],
))

registry.register(Capability(
    name="redis-cache",
    version="3.0.0",
    provides=["storage", "cache"],
    requires=["network"],
))

# Find everything that provides "network"
network_caps = registry.match("network")
print([c.name for c in network_caps])
```

**Expected output:**
```
['http-server', 'grpc-server']
```

### Resolving a List of Needs

```python
needs = ["http", "cache"]
resolved = registry.resolve(needs)
for cap in resolved:
    print(f"{cap.name} v{cap.version} -> provides {cap.provides}")
```

**Expected output:**
```
http-server v1.2.0 -> provides ['network', 'http']
redis-cache v3.0.0 -> provides ['storage', 'cache']
```

---

## Cellular Automata

Create grids with pluggable rules and run simulations.

### Diffusion Simulation

```python
from si_runtime.cell import Cell, Grid

def diffuse(state, neighbors):
    if not neighbors:
        return state
    return sum(neighbors) / len(neighbors)

cells = [
    Cell(state=10.0, neighbors=[1]),
    Cell(state=0.0, neighbors=[0, 2]),
    Cell(state=0.0, neighbors=[1]),
]

grid = Grid(cells, diffuse)
history = grid.run(5)
print("Step totals:", [round(h, 2) for h in history])
print("Final states:", [round(c.state, 2) for c in cells])
```

**Expected output:**
```
Step totals: [10.0, 10.0, 10.0, 10.0, 10.0]
Final states: [3.33, 3.33, 3.33]
```

### Factory: Ring Grid

```python
from si_runtime.cell import new_grid

# 10-cell ring, each cell averages its 2 neighbors
def avg_rule(state, neighbors):
    if not neighbors:
        return state
    return (state + sum(neighbors)) / (1 + len(neighbors))

grid = new_grid(10, avg_rule, initial=1.0, connectivity=1)
# Seed cell 0 with a different value
grid.cells[0].state = 5.0

history = grid.run(20)
print(f"After 20 steps: total={sum(c.state for c in grid.cells):.2f}")
```

**Expected output:**
```
After 20 steps: total=14.00
```

---

## Agent Homeostasis

Agents maintain gauges and self-regulate toward targets using PID control.

### Basic Gauge Management

```python
from si_runtime import Agent

agent = Agent(id="thermostat", state={"room": "living"})
agent.add_gauge("temperature", 15.0)
agent.add_gauge("humidity", 0.4)

print(agent.gauges)
```

**Expected output:**
```
{'temperature': 15.0, 'humidity': 0.4}
```

### PID Homeostasis

```python
agent = Agent(id="thermo")
agent.add_gauge("temperature", 10.0)

# Regulate temperature toward 22.0
for step in range(100):
    agent.homeostasis({"temperature": 22.0}, dt=0.1)

print(f"Temperature: {agent.gauges['temperature']:.2f} (target: 22.0)")
```

**Expected output:**
```
Temperature: 22.00 (target: 22.0)
```

---

## Fleet Orchestration

Combine agents with adjacency and budget tracking for fleet-level operations.

### Creating a Fleet

```python
from si_runtime import Fleet, Agent, Budget, AgentBudget

fleet = Fleet()

# Add agents
for i in range(4):
    a = Agent(id=f"node-{i}")
    b = AgentBudget(id=f"node-{i}", budget=Budget(total=100.0, gamma=60.0, eta=40.0))
    fleet.add_agent(a, b)

# Set up adjacency (ring)
from si_runtime import adjacency_matrix
edges = [(i, (i + 1) % 4, 1.0) for i in range(4)]
fleet.adjacency = adjacency_matrix(4, edges)

report = fleet.health_report()
print(report)
```

**Expected output:**
```
{'agent_count': 4, 'spectral_ranking': [0, 1, 2, 3], 'conservation_violations': 0, 'total_gauges': 0}
```

### Fleet Spectral Ranking

```python
# Line graph: 0-1-2-3 (middle nodes more central)
from si_runtime import adjacency_matrix
fleet = Fleet()
fleet.agents = [Agent(id=f"n{i}") for i in range(4)]
fleet.adjacency = adjacency_matrix(4, [(0, 1, 1.0), (1, 2, 1.0), (2, 3, 1.0)])

rank = fleet.spectral_rank()
print(f"Most central: node-{rank[0]}")
```

**Expected output:**
```
Most central: node-1
```

### Fleet with Budget Auditing

```python
fleet = Fleet()

fleet.add_agent(
    Agent(id="reliable"),
    AgentBudget(id="reliable", budget=Budget(total=50.0, gamma=30.0, eta=20.0)),
)

fleet.add_agent(
    Agent(id="drifty"),
    AgentBudget(id="drifty", budget=Budget(total=50.0, gamma=10.0, eta=10.0)),
)

violations = fleet.conservation_audit()
print(f"Violations: {len(violations)}")
for v in violations:
    print(f"  {v.agent_id}: delta={v.delta}")
```

**Expected output:**
```
Violations: 1
  drifty: delta=30.0
```

### Full Health Report

```python
fleet = Fleet()
a = Agent(id="sensor-1")
a.add_gauge("cpu", 0.6)
a.add_gauge("mem", 0.8)

fleet.add_agent(
    a,
    AgentBudget(id="sensor-1", budget=Budget(total=100.0, gamma=60.0, eta=40.0)),
)

report = fleet.health_report()
for k, v in report.items():
    print(f"  {k}: {v}")
```

**Expected output:**
```
  agent_count: 1
  spectral_ranking: [0]
  conservation_violations: 0
  total_gauges: 2
```

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest -v
```

## Module Reference

| Module | Description |
|--------|-------------|
| `si_runtime.conservation` | Budget tracking with gamma+eta invariant enforcement |
| `si_runtime.spectral` | Eigenvector centrality and spectral ranking |
| `si_runtime.capability` | Capability registration and dependency resolution |
| `si_runtime.cell` | Cellular automata with pluggable rules |
| `si_runtime.agent` | Agents with PID-gauged homeostasis |
| `si_runtime.fleet` | Multi-agent orchestration layer |

## License

MIT
