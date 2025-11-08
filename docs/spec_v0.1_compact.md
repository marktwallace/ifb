# IRREPnet Implementation Spec — v0.1 (Compact, Single-Channel)

**Goal:** Define the minimal, framework-ready specification for IRREPnet v0.1.  
This document governs **all implementations**. No interpretation or physics background assumed.

---

## 1) Model Summary

| Concept | Definition |
|---|---|
| Phase group | `Z_k`, where `k` is an integer in `[2..256]`, stored as `u8` mod `k`. |
| Directed graph | `ED` directed edges, each `e` has `src[e]` and `dst[e]`. |
| State | `counts[e, g]` = integer count of microhistories on edge `e` in phase class `g`. |
| Update | Local, integer-only propagation with circular phase shift + mask. |
| Time | Execution order defined by a DAG of update layers. |
| Measurement | Phasor sum over phase bins → square amplitude → normalize. |

This version is **single-channel** (no fusion multiplicity).

---

## 2) Data Structures

```
k: int                 # phase group size
V: int                 # number of nodes
ED: int                # number of directed edges
```

### Nodes
```
nodes:
  gauge_phase[v]: u8   # optional; default 0
```

### Directed Edges
```
directed_edges[e]:
  src[e]: int
  dst[e]: int
  edge_ref[e]: int     # index into edges table
```

### Edge Phase Offsets
```
edges[edge_ref]:
  phase_offset: u8     # added during propagation (mod k)
```

### State Buffer
```
counts[e, g]: int32    # shape [ED, k], g ∈ [0..k-1]
```

### Fusion Mask (Single Channel)
```
fusion_mask[e, g]: u8 (0 or 1)   # shape [ED, k]
```

### DAG Schedule
```
dag.layers: List[List[edge_id]]
dag.repeat: int >= 1
```

### Measurement
```
readouts:
  - name: str
    readout_edges: List[edge_id]
```

---

## 3) Update Rule (One Layer)

For each `e` in `layer` (parallelizable):

```
u = src[e]
v = dst[e]

Δ = (gauge_phase[u] - gauge_phase[v] + phase_offset[edge_ref[e]]) mod k

# Circular phase rotate
shifted[g_out] = counts[e, (g_out - Δ) mod k]

# Apply mask
allowed[g_out] = shifted[g_out] if fusion_mask[e, g_out] == 1 else 0
```

Accumulate to all outgoing edges from `v`:
```
for f in out_edges(v):
    counts_next[f, g_out] += allowed[g_out]
```

After finishing the layer:
```
swap(counts, counts_next)
zero(counts_next)
```

One **tick** = apply all layers in order `dag.repeat` times.

---

## 4) Measurement

For each readout:
```
n_g = Σ_e∈readout_edges counts[e, g]
A  = Σ_g n_g * exp(2πi * g / k)
P  = |A|^2
normalize across readouts if mutually exclusive
```

Measurement is the **only** stage using floats.

---

## 5) Invariants

- All state evolution is **integer-only**.
- Phases are always computed **mod k**.
- `fusion_mask == 0` must block amplitude contribution.
- Uniform shift in all `gauge_phase[v]` values must **not** change measurement outcomes.
- No directed edge may appear twice in the same DAG layer.
- Double-buffering is required to avoid read/write conflicts.

---

## 6) Runtime Binding for v0.1

Default implementation target:

```
Language: Python 3.12+
Framework: PyTorch >= 2.2
Device priority:
  1. mps
  2. cuda
  3. cpu

counts: torch.int32  (or int64 for safety)
fusion_mask: torch.uint8
phase and Δ arithmetic: uint8 mod k
accumulation: torch.scatter_add_ or torch.index_add_
gradients: disabled (use torch.no_grad())
```

---

## 7) Required Public API

```
class IRREPnetSim:
    def __init__(self, scenario_file): ...
    def validate(self): ...
    def reset(self): ...
    def step(self): ...        # run one full tick
    def measure(self): ...
    def export_state(self): ...
```

---

## 8) Minimal Test Scenarios

Simulation must reproduce:
- **two_path_v01**: interference pattern varies with gauge on one arm
- **triangle_loop_v01**: uniform gauge shift invariance holds
- **chain_momentum_v01**: repeating phase structure propagates as momentum

---

End of IRREPnet v0.1 compact spec.
