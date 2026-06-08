# INTEGRATION.md — si-runtime-python

Cross-language integration guide for the **SuperInstance Python runtime** (`si-runtime-python`).
This document shows the same conservation budget operation in all 7 supported languages,
how this library connects to the broader SuperInstance ecosystem, and FFI binding patterns.

---

## Table of Contents

1. [Same Operation in 7 Languages](#1-same-operation-in-7-languages)
2. [Cross-Repo Integration](#2-cross-repo-integration)
3. [FFI Bindings](#3-ffi-bindings)

---

## 1. Same Operation in 7 Languages

The canonical operation: **create a conservation budget of C=1000, allocate gamma=600 and eta=400, verify the invariant γ+η=C, then transfer budget between agents.**

### Python (si-runtime-python — this repo)

```python
from si_runtime import Budget, AgentBudget, audit, transfer

# Create budget with total C = 1000
budget_a = Budget(total=1000.0, gamma=600.0, eta=400.0)

# Verify the conservation invariant: gamma + eta == total
assert abs(budget_a.gamma + budget_a.eta - budget_a.total) < 1e-9
print(f"budget_a: gamma={budget_a.gamma} eta={budget_a.eta} total={budget_a.total}")

# Create agent budgets and allocate
agent_a = AgentBudget(id="agent-a", budget=budget_a)
agent_a.allocate(500.0)

budget_b = Budget(total=1000.0, gamma=300.0, eta=700.0)
agent_b = AgentBudget(id="agent-b", budget=budget_b)
agent_b.allocate(200.0)

# Transfer budget between agents (preserves invariants)
transfer(agent_a, agent_b, 50.0)
print(f"agent_a remaining={agent_a.remaining}")
print(f"agent_b remaining={agent_b.remaining}")

# Fleet-wide audit
violations = audit([agent_a, agent_b])
print(f"Conservation violations: {len(violations)}")
for v in violations:
    print(f"  {v.agent_id}: expected={v.expected} actual={v.actual}")
```

### Rust (conservation-law-rs — reference implementation)

```rust
use conservation_law::ConservationBudget;

fn main() {
    let mut budget = ConservationBudget::new(1000.0);
    budget.allocate(600.0, 400.0).expect("allocation failed");

    let audit = budget.audit();
    assert!((audit.gamma + audit.eta - audit.total).abs() < 1e-10);
    println!("gamma={} eta={} total={}", audit.gamma, audit.eta, audit.total);

    budget.transfer("gamma", "eta", 50.0).expect("transfer failed");
    let audit = budget.audit();
    println!("After transfer: gamma={} eta={}", audit.gamma, audit.eta);
}
```

### C (si-core-c)

```c
#include "si_core.h"
#include <stdio.h>
#include <assert.h>

int main(void) {
    si_init();

    SiBudget *budget = budget_create(1000.0);
    SiError err = budget_allocate(budget, 600.0, 400.0);
    assert(err == SI_OK);

    BudgetReport rpt = budget_audit(budget);
    assert(rpt.violation == 0);
    assert(rpt.gamma + rpt.eta == rpt.total_budget);
    printf("gamma=%.1f eta=%.1f total=%.1f\n",
           rpt.gamma, rpt.eta, rpt.total_budget);

    err = budget_transfer(budget, 0, 1, 50.0);
    assert(err == SI_OK);

    rpt = budget_audit(budget);
    printf("After transfer: gamma=%.1f eta=%.1f\n", rpt.gamma, rpt.eta);

    budget_free(budget);
    si_shutdown();
    return 0;
}
```

### TypeScript (si-runtime-js)

```typescript
import { ConservationBudget } from 'si-runtime-js';

const budget = new ConservationBudget(1000);
budget.allocate(600, 400);

const report = budget.audit();
console.log(`gamma=${report.gamma} eta=${report.eta} total=${report.C}`);

budget.transfer('gamma', 'eta', 50);
const after = budget.audit();
console.log(`After transfer: gamma=${after.gamma} eta=${after.eta}`);
```

### Zig (si-runtime-zig)

```zig
const conservation = @import("conservation.zig");

pub fn main() !void {
    var budget = conservation.ConservationBudget.init(1000.0);
    try budget.allocate(600.0, 400.0);
    const report = try budget.audit();
    std.debug.print("gamma={d:.1} eta={d:.1} total={d:.1}\n",
        .{ report.gamma, report.eta, report.total });
    try budget.transfer(true, 50.0);
}
```

### Go (si-runtime-go)

```go
package main

import siruntime "github.com/SuperInstance/si-runtime-go"

func main() {
    budget := siruntime.NewBudget(1000)
    budget.Allocate(600, 400)
    fmt.Printf("gamma=%.1f eta=%.1f total=%.1f\n",
        budget.Gamma, budget.Eta, budget.Total)
    budget.Transfer(50)
}
```

### WASM (si-runtime-wasm — from JavaScript)

```javascript
import init, { Budget } from 'si-runtime-wasm';

async function run() {
    await init();
    const budget = new Budget(1000);
    budget.allocate(300);
    budget.transfer_gamma_to_eta(50);
    console.log(`Audit: ${budget.audit()}, gamma=${budget.gamma()}, eta=${budget.eta()}`);
}
```

---

## 2. Cross-Repo Integration

### conservation-law-rs (Mathematical Foundation)

The Python `Budget` dataclass mirrors the Rust `ConservationBudget` struct. The
`validate_budget()` function enforces the same γ+η=C invariant defined in
`conservation-law-rs`. Any changes to the conservation law algebra should propagate
from Rust → Python.

**Connection points:**
- `Budget(total, gamma, eta)` ↔ `ConservationBudget::new(C)` + `allocate(γ, η)`
- `validate_budget()` ↔ `ConservationBudget::audit()`
- `transfer()` ↔ `ConservationBudget::transfer()`

### spectral-fleet-rs (Fleet Ranking)

The Python `spectral_rank()` function uses the same power-iteration algorithm as
`spectral-fleet-rs`. Python agents contribute eigenvector centrality scores to fleet-wide
ranking through the shared adjacency matrix format.

**Connection points:**
- `adjacency_matrix()` builds matrices compatible with Rust's spectral solver
- `spectral_rank()` returns ranked indices matching the Rust `rank()` output format
- `power_iteration()` uses identical convergence criteria (tolerance, max iterations)

### si-cli (CLI Discovery)

`si-cli` discovers Python agents by importing `si_runtime` and calling `Fleet.health_report()`.
Python agents register their capabilities and budgets, and the CLI queries them for
fleet coordination.

**Connection points:**
- `Fleet.health_report()` → CLI dashboard display
- `Capability` TOML parsing → CLI `discover` command
- `AgentBudget` state → CLI `status` command

### si-fleet-api (REST API Layer)

The REST API exposes Python agent state as JSON. The `Fleet` class's
`conservation_audit()` method provides violation data that the API serves at
`GET /fleet/audit`. Python agents are first-class fleet members.

**Connection points:**
- `Fleet.conservation_audit()` → `GET /fleet/audit`
- `Fleet.spectral_rank()` → `POST /fleet/rank`
- `Agent` state/gauges → `GET /agents/:id`
- `Budget` serialization → `GET /agents/:id/budget`

### Supabase Fleet Registry (Data Backend)

Python agents persist their state to Supabase via the fleet API. The `AgentBudget` and
`Budget` dataclasses map directly to Supabase table schemas.

**Connection points:**
- `Budget(total, gamma, eta)` → `agent_budgets` table row
- `Agent.gauges` → `agent_gauges` JSONB column
- `Violation` dataclass → `conservation_violations` table
- `Fleet.health_report()` output → `fleet_health` materialized view

### sunset-ecosystem (Fleet Coordination)

`sunset-ecosystem` coordinates multi-fleet operations. Python agents participate by
exposing their budgets and spectral rankings through the Fleet class, which
sunset-ecosystem queries for rebalancing decisions.

**Connection points:**
- `Fleet.spectral_rank()` for fleet-wide agent ordering
- `transfer()` for cross-agent budget movement during rebalancing
- `Agent.homeostasis()` for PID-regulated gauge maintenance
- `Fleet.add_agent()` for dynamic fleet membership

---

## 3. FFI Bindings

### Calling si-runtime-python from Rust (via PyO3)

```rust
use pyo3::prelude::*;

fn call_python_runtime() -> PyResult<()> {
    Python::with_gil(|py| {
        let si = py.import_bound("si_runtime")?;
        let budget_cls = si.getattr("Budget")?;
        let budget = budget_cls.call1((1000.0, 600.0, 400.0))?;

        let gamma: f64 = budget.getattr("gamma")?.extract()?;
        let eta: f64 = budget.getattr("eta")?.extract()?;
        println!("Python budget: gamma={} eta={}", gamma, eta);

        // Run fleet audit
        let audit = si.getattr("audit")?;
        let violations = audit.call1((vec![budget],))?;
        let count: usize = violations.len()?;
        println!("Violations: {}", count);
        Ok(())
    })
}
```

### Calling si-runtime-python from C (via Python C API)

```c
#include <Python.h>

void call_python_budget(void) {
    Py_Initialize();

    PyObject *module = PyImport_ImportModule("si_runtime");
    PyObject *budget_cls = PyObject_GetAttrString(module, "Budget");

    // Budget(total=1000.0, gamma=600.0, eta=400.0)
    PyObject *args = Py_BuildValue("(ddd)", 1000.0, 600.0, 400.0);
    PyObject *budget = PyObject_CallObject(budget_cls, args);

    PyObject *gamma = PyObject_GetAttrString(budget, "gamma");
    printf("Python gamma = %f\n", PyFloat_AsDouble(gamma));

    Py_DECREF(gamma);
    Py_DECREF(budget);
    Py_DECREF(args);
    Py_DECREF(budget_cls);
    Py_DECREF(module);
    Py_Finalize();
}
```

### Calling si-runtime-python from TypeScript/Node.js (via pythonia)

```typescript
import { python } from 'pythonia';

async function callPython() {
    const si = await python('si_runtime');
    const budget = await si.Budget(1000, 600, 400);
    console.log(`Python gamma=${await budget.gamma} eta=${await budget.eta}`);

    const violations = await si.audit([budget]);
    console.log(`Violations: ${await violations.length}`);

    python.exit();
}
```

### Calling si-runtime-python from Go (via CPython embedding)

```go
package main

/*
#cgo pkg-config: python3-embed
#include <Python.h>
*/
import "C"
import "fmt"

func callPythonBudget() {
    C.Py_Initialize()

    mod := C.PyImport_ImportModule(C.CString("si_runtime"))
    cls := C.PyObject_GetAttrString(mod, C.CString("Budget"))
    args := C.Py_BuildValue(C.CString("(ddd)"), 1000.0, 600.0, 400.0)
    budget := C.PyObject_CallObject(cls, args)

    gamma := C.PyObject_GetAttrString(budget, C.CString("gamma"))
    fmt.Printf("Python gamma = %f\n", C.PyFloat_AsDouble(gamma))

    C.Py_DECREF(gamma)
    C.Py_DECREF(budget)
    C.Py_DECREF(args)
    C.Py_DECREF(cls)
    C.Py_DECREF(mod)
    C.Py_Finalize()
}
```

### Calling si-runtime-python from Zig

```zig
// Use CPython C API via @cImport
const py = @cImport(@cInclude("Python.h"));

pub fn callPythonBudget() !void {
    py.Py_Initialize();

    const mod = py.PyImport_ImportModule("si_runtime");
    const cls = py.PyObject_GetAttrString(mod, "Budget");
    const args = py.Py_BuildValue("(ddd)", 1000.0, 600.0, 400.0);
    const budget = py.PyObject_CallObject(cls, args);

    const gamma = py.PyObject_GetAttrString(budget, "gamma");
    std.debug.print("Python gamma = {d}\n", .{py.PyFloat_AsDouble(gamma)});

    py.Py_DECREF(gamma);
    py.Py_DECREF(budget);
    py.Py_DECREF(args);
    py.Py_DECREF(cls);
    py.Py_DECREF(mod);
    py.Py_Finalize();
}
```

### Calling C from Python (ctypes bridge to si-core-c)

```python
import ctypes

lib = ctypes.CDLL("./libsi_core.so")
lib.si_init()

lib.budget_create.restype = ctypes.c_void_p
budget = lib.budget_create(1000.0)

lib.budget_allocate.restype = ctypes.c_int
err = lib.budget_allocate(budget, 600.0, 400.0)
assert err == 0

lib.budget_free(budget)
lib.si_shutdown()
```

### Calling Rust from Python (via C ABI)

```python
import ctypes

# Load Rust library compiled with C ABI exports
lib = ctypes.CDLL("./libconservation_law.so")

lib.conservation_budget_new.restype = ctypes.c_void_p
lib.conservation_budget_new.argtypes = [ctypes.c_double]

budget = lib.conservation_budget_new(1000.0)
```

---

## Integration Test Matrix

| From → To | C | Rust | Python | TypeScript | Zig | Go | WASM |
|---|---|---|---|---|---|---|---|
| **Python** | ctypes / C API | PyO3 / ctypes | ✅ native | pythonia | C API | C API | N/A |
| **C** | ✅ native | cdylib | C API embed | ffi-napi | `@cImport` | cgo | emscripten |
| **Rust** | extern "C" | ✅ native | PyO3 | wasm-bindgen | C ABI | C ABI | wasm-bindgen |
| **TypeScript** | ffi-napi | wasm-bindgen | pythonia | ✅ native | N/A | N/A | wasm API |
| **Zig** | `@cImport` | C ABI | C API embed | N/A | ✅ native | C ABI | N/A |
| **Go** | cgo | C ABI | C API embed | N/A | C ABI | ✅ native | N/A |
| **WASM** | emscripten | wasm-bindgen | N/A | JS import | N/A | N/A | ✅ native |

---

## Python Module API Summary

| Module | Class/Function | Description |
|---|---|---|
| `conservation` | `Budget(total, gamma, eta)` | Conservation budget with invariant |
| `conservation` | `AgentBudget(id, budget)` | Per-agent budget with allocate/spend |
| `conservation` | `validate_budget(b)` | Check γ+η=C invariant |
| `conservation` | `transfer(from, to, amount)` | Move budget between agents |
| `conservation` | `audit(budgets)` → `list[Violation]` | Fleet-wide audit |
| `spectral` | `adjacency_matrix(n, edges)` | Build NxN adjacency matrix |
| `spectral` | `power_iteration(matrix)` | Dominant eigenvector |
| `spectral` | `spectral_rank(adj)` | Node indices by centrality |
| `capability` | `Capability` | Parsed TOML capability |
| `capability` | `Registry` | Capability registry |
| `cell` | `Cell` / `Grid` / `new_grid()` | Cellular automata |
| `agent` | `Agent(id)` | Agent with PID homeostasis |
| `fleet` | `Fleet` | Multi-agent orchestration |

---

*Generated for SuperInstance cross-language integration — si-runtime-python v0.1.0*
