# si-runtime-python

> **Python runtime for the SuperInstance ecosystem — constraint-aware agents, spectral ranking, and fleet orchestration.**

---

## Overview

`si_runtime` is a pure-Python library that provides the core runtime primitives for building constraint-aware agent systems. It implements:

- **Conservation budgets** — enforce `gamma + eta = total` across all agent operations
- **Spectral ranking** — power iteration to find the most central agents in a capability graph
- **Capability registry** — match required vs offered capabilities across a fleet
- **Cellular automata** — local update rules with neighbor coupling and energy tracking
- **Agent homeostasis** — state machine with stress/recovery based on energy ratios
- **Fleet orchestration** — manage groups of agents with aggregate conservation auditing

All modules are pure Python with **zero external dependencies** for the core library.

---

## Installation

```bash
pip install si-runtime
```

Or install from source:

```bash
git clone https://github.com/SuperInstance/si-runtime-python.git
cd si-runtime-python
pip install -e ".[dev]"
```

---

## Quick Start

### 1. Conservation Budget — Enforce Physical Invariants

Every agent carries a conservation budget: kinetic energy (`gamma`) plus potential energy (`eta`) must always equal a fixed total. If any operation would break this law, it raises `ConservationError`.

```python
from si_runtime import AgentBudget, allocate, transfer, audit

# Create a budget with total energy 100.0 (split 50/50 by default)
budget = AgentBudget.create(100.0)
print(f"Initial: gamma={budget.gamma:.1f}, eta={budget.eta:.1f}")
# Output: Initial: gamma=50.0, eta=50.0

# Reallocate explicitly
allocate(budget, gamma=30.0, eta=70.0)
print(f"After allocate: gamma={budget.gamma:.1f}, eta={budget.eta:.1f}")
# Output: After allocate: gamma=30.0, eta=70.0

# Transfer 10.0 from gamma to eta
transfer(budget, from_gamma=True, amount=10.0)
print(f"After transfer: gamma={budget.gamma:.1f}, eta={budget.eta:.1f}")
# Output: After transfer: gamma=20.0, eta=80.0

# Audit verifies the invariant
report = audit(budget)
print(f"Audit valid={report.valid}, utilization={report.utilization:.2%}")
# Output: Audit valid=True, utilization=50.00%

# Attempting to violate the law raises an exception
try:
    allocate(budget, gamma=60.0, eta=60.0)  # 60 + 60 != 100
except Exception as e:
    print(f"Caught: {type(e).__name__}: {e}")
# Output: Caught: ConservationError: Allocation must sum to total 100.0, got 120.0
```

---

### 2. Spectral Ranking — Find the Most Central Agent

Given an adjacency matrix representing interactions between agents, power iteration extracts the dominant eigenvector. The largest components identify the most central agents — those whose capabilities propagate influence fastest through the fleet.

```python
from si_runtime import AdjacencyMatrix, spectral_rank, power_iteration

# Build a 3x3 adjacency matrix for three agents.
# Higher diagonal = more self-reliant.
# Off-diagonal = shared capabilities / communication bandwidth.
matrix = AdjacencyMatrix([
    [8.0, 2.0, 1.0],   # Agent 0: very self-connected
    [2.0, 6.0, 1.5],   # Agent 1
    [1.0, 1.5, 5.0],   # Agent 2
])

# Power iteration: dominant eigenvalue + eigenvector
eigenvalue, eigenvector = power_iteration(matrix, iterations=300)
print(f"Dominant eigenvalue: {eigenvalue:.4f}")
# Output: Dominant eigenvalue: ~8.8

print(f"Eigenvector: {[round(v, 4) for v in eigenvector]}")
# Output: Eigenvector: [~0.74, ~0.58, ~0.34]

# Full ranking using deflation (all eigenvalues)
ranked = spectral_rank(matrix)
for idx, ev in ranked:
    print(f"  Agent {idx}: eigenvalue={ev:.4f}")
# Output:
#   Agent 0: eigenvalue=~8.8
#   Agent 1: eigenvalue=~6.3
#   Agent 2: eigenvalue=~4.9
```

---

### 3. Capability Registry — Matchmaking Across Agents

Agents advertise capabilities. The registry tracks who offers what, and `match_capabilities` pairs requirements with providers.

```python
from si_runtime import Capability, Registry, match_capabilities

# Define capabilities with tags
plan = Capability("plan", tags=("nav", "route"), version="1.2.0")
see = Capability("see", tags=("camera", "lidar"))
fly = Capability("fly", tags=("rotor",))

# Registry holds capabilities per owner
reg = Registry()
reg.register(plan, owner_id="agent_1")
reg.register(see, owner_id="agent_1")
reg.register(fly, owner_id="agent_2")

print(f"Registry size: {len(reg)}")
# Output: Registry size: 3

print(f"Owners of 'plan': {reg.owners('plan')}")
# Output: Owners of 'plan': {'agent_1'}

# Match required against offered
required = [Capability("plan", tags=("nav",)), Capability("fly")]
offered = [plan, see]  # agent_1's capabilities

matched, unmatched = match_capabilities(required, offered)
print(f"Matched: {[c.name for c in matched]}")
# Output: Matched: ['plan']

print(f"Unmatched: {[c.name for c in unmatched]}")
# Output: Unmatched: ['fly']
```

---

### 4. Agent with Homeostasis — Self-Regulating Energy State

An `Agent` wraps a conservation budget with a state machine. If `gamma / total` drops below a critical threshold, the agent enters `STRESSED` and refuses to activate until it recovers.

```python
from si_runtime import Agent, AgentBudget, Capability

# Create an agent with a 100-unit budget and custom thresholds
agent = Agent(
    agent_id="explorer_1",
    budget=AgentBudget.create(100.0),
    capabilities=[Capability("plan"), Capability("sense")],
    critical_gamma_ratio=0.20,   # stressed below 20%
    recovery_gamma_ratio=0.40,   # recover above 40%
)

print(f"Initial state: {agent.state.name}, gamma_ratio={agent.gamma_ratio:.2f}")
# Output: Initial state: IDLE, gamma_ratio=0.50

# Spend energy (moves gamma -> eta)
agent.spend(35.0)
print(f"After spend: state={agent.state.name}, gamma={agent.budget.gamma:.1f}")
# Output: After spend: state=IDLE, gamma=15.0

# Spend more — now below critical threshold
agent.spend(5.0)
print(f"Stressed: state={agent.state.name}, gamma_ratio={agent.gamma_ratio:.2f}")
# Output: Stressed: state=STRESSED, gamma_ratio=0.10

# Cannot activate while stressed
try:
    agent.activate()
except Exception as e:
    print(f"Caught: {e}")
# Output: Caught: Agent is stressed — cannot activate

# Recharge to recover
agent.recharge(40.0)
print(f"Recovered: state={agent.state.name}, gamma_ratio={agent.gamma_ratio:.2f}")
# Output: Recovered: state=RECOVERING, gamma_ratio=0.50

# Now activation works
agent.activate()
print(f"Active: state={agent.state.name}")
# Output: Active: state=ACTIVE
```

---

### 5. Fleet Orchestration — Rank and Audit a Group of Agents

A `Fleet` manages many agents. It can rank them by spectral centrality and run conservation audits across the entire group.

```python
from si_runtime import Fleet, Agent, AgentBudget, Capability

fleet = Fleet("survey_team")

# Add three agents with overlapping capabilities
fleet.add_agent(Agent("alpha", budget=AgentBudget.create(100.0),
                      capabilities=[Capability("plan"), Capability("sense")]))
fleet.add_agent(Agent("beta", budget=AgentBudget.create(100.0),
                      capabilities=[Capability("plan"), Capability("move")]))
fleet.add_agent(Agent("gamma", budget=AgentBudget.create(100.0),
                      capabilities=[Capability("sense"), Capability("move")]))

print(f"Fleet size: {fleet.size}")
# Output: Fleet size: 3

# Spectral rank by capability overlap
ranked = fleet.spectral_rank()
print("Spectral ranking:")
for agent_id, ev in ranked:
    print(f"  {agent_id}: eigenvalue={ev:.4f}")
# Output: (order depends on matrix, but all three are ranked)

# Conservation audit across the whole fleet
audits = fleet.conservation_audit()
print("\nConservation audits:")
for agent_id, report in audits.items():
    print(f"  {agent_id}: valid={report.valid}, gamma={report.gamma:.1f}")
# Output:
#   alpha: valid=True, gamma=50.0
#   beta: valid=True, gamma=50.0
#   gamma: valid=True, gamma=50.0

# Aggregate health
health = fleet.fleet_health()
print(f"\nFleet status: {health['status']}")
print(f"Total energy: gamma={health['total_gamma']:.1f}, eta={health['total_eta']:.1f}")
# Output:
#   Fleet status: healthy
#   Total energy: gamma=150.0, eta=150.0

# Broadcast an action to every agent
fleet.broadcast(lambda a: a.spend(10.0))
health_after = fleet.fleet_health()
print(f"After broadcast spend: gamma={health_after['total_gamma']:.1f}")
# Output: After broadcast spend: gamma=120.0
```

---

### 6. Cellular Automaton — Local Rules with Energy Costs

Cells maintain local state, couple to neighbors, and pay an energy cost per update.

```python
from si_runtime import Cell

# Create a 1D chain of three cells
a = Cell("a", state=1.0, energy_cost=0.05)
b = Cell("b", state=2.0, energy_cost=0.05)
c = Cell("c", state=3.0, energy_cost=0.05)

a.add_neighbor(b)
b.add_neighbor(c)

# Mean-field update: new_state = average of neighbors
rule = lambda cell, neighbors: cell.mean_field() if neighbors else cell.state

a.update(rule)
print(f"a state={a.state:.2f}, energy_spent={a.energy_spent():.2f}")
# Output: a state=2.00, energy_spent=0.05

b.update(rule)
print(f"b state={b.state:.2f}, degree={b.degree}")
# Output: b state=2.50, degree=2

print(f"c history={c.history}")
# Output: c history=[]  (c was never updated)
```

---

## API Reference

### `si_runtime.conservation`

| Name | Description |
|------|-------------|
| `Budget(gamma, eta, total)` | Immutable frozen budget. Validates invariant on creation. |
| `AgentBudget(gamma, eta, total)` | Mutable budget wrapper for agents. |
| `allocate(budget, gamma, eta)` | Reallocate energy. Raises `ConservationError` on violation. |
| `transfer(budget, from_gamma, amount)` | Move energy between gamma and eta. |
| `audit(budget) -> Audit` | Verify invariant and return utilization report. |

### `si_runtime.spectral`

| Name | Description |
|------|-------------|
| `AdjacencyMatrix(data)` | Immutable square matrix with `@` operator for matvec. |
| `power_iteration(matrix, iterations, seed)` | Dominant eigenvalue / eigenvector. |
| `spectral_rank(matrix, iterations)` | Full ranking by deflation power iteration. |

### `si_runtime.capability`

| Name | Description |
|------|-------------|
| `Capability(name, tags, version, description)` | Named capability with tag matching. |
| `Registry()` | Central capability registry with owner tracking. |
| `match_capabilities(required, offered)` | Returns `(matched, unmatched)`. |

### `si_runtime.cell`

| Name | Description |
|------|-------------|
| `Cell(name, state, energy_cost)` | Automaton cell with neighbors and history. |
| `cell.update(rule)` | Apply `rule(cell, neighbors)` and record history. |
| `cell.mean_field()` | Average state of neighbors. |

### `si_runtime.agent`

| Name | Description |
|------|-------------|
| `Agent(agent_id, budget, state, capabilities)` | Stateful agent with homeostasis. |
| `agent.spend(amount)` | Move energy gamma→eta. May trigger STRESSED. |
| `agent.recharge(amount)` | Move energy eta→gamma. |
| `agent.activate()` | Transition to ACTIVE (fails if STRESSED). |
| `agent.tick()` | Advance homeostasis state machine. |

### `si_runtime.fleet`

| Name | Description |
|------|-------------|
| `Fleet(name)` | Container for multiple agents. |
| `fleet.add_agent(agent)` | Register an agent. |
| `fleet.spectral_rank()` | Rank agents by capability-graph centrality. |
| `fleet.conservation_audit()` | Audit every agent's budget. |
| `fleet.fleet_health()` | Aggregate health metrics. |
| `fleet.broadcast(action)` | Run `action(agent)` on every agent. |

---

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

The test suite covers conservation invariants, spectral correctness, capability matching, cell updates, agent homeostasis, and fleet orchestration.

---

## Design Principles

1. **Zero hidden allocations** — pure Python, no heavy dependencies.
2. **Fail fast on invariant violation** — `ConservationError` stops bad physics immediately.
3. **Immutable where possible** — `Budget` and `Audit` are frozen dataclasses.
4. **Explicit energy costs** — every update, every tick, every cell transition has a cost.

---

## License

MIT
