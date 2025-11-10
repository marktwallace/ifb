# Channel System Specification — v0.2
Project: IFB — Engine: `irrepnet`

## Overview
This document defines the canonical channel set and coupling rules for the **lepton + photon + muon** IFB model used in the muonium cloud experiment.

Channels here are **irreps**: there is exactly one way to be each particle. No internal decomposition exists below channels.

## Channel List

```
channels:
  - { name: e_minus, charge: -1, neutral: false }
  - { name: e_plus,  charge: +1, neutral: false }
  - { name: mu_plus, charge: +1, neutral: false }
  - { name: gamma,   charge:  0, neutral: true  }
```

- `charge` is used only for **consistency constraints**, not forces.
- `neutral: true` indicates a channel whose propagation is unaffected by gauge offsets.

## State Representation
```
counts[edge, channel, phase] ∈ ℕ
phase ∈ Z_k
```
Propagation applies a local phase shift:
```
phase_new = (phase_old + edge.phase_offset + gauge(src) - gauge(dst)) % k
```

## Fusion Masks
A **fusion mask** restricts which phases a channel may occupy on a given edge.
Example:
```
- { edge_id: 6, channel: mu_plus, allow_phases: [0, 4] }
```
This creates **discrete orbital quantization**.

## Coupling Rules (Local Updating Dynamics)

### Bremsstrahlung
```
name: brems_emit
scope: { nodes_any: ["scatter_zone"] }
in:   [{ ch: e_minus, min: 1 }]
out:  [{ ch: e_minus, add: 1 }, { ch: gamma, add: 1 }]
phase: { gamma: "delta", e_minus: "inherit" }
```

### Positronium Loop Transition + Gamma Emission
```
name: ps_transition_emit
scope: { nodes_any: ["scatter_zone"], out_edges_any: ["positronium"] }
in:   [{ ch: e_minus, min: 1 }, { ch: e_plus, min: 1 }]
out:  [{ ch: e_minus, add: 1 }, { ch: e_plus, add: 1 }, { ch: gamma, add: 1 }]
phase: { gamma: "fixed:4" }
```

### Muonium Loop Transition + Gamma Emission
```
name: muonium_transition_emit
scope: { nodes_any: ["scatter_zone"], out_edges_any: ["muonium"] }
in:   [{ ch: e_minus, min: 1 }, { ch: mu_plus, min: 1 }]
out:  [{ ch: e_minus, add: 1 }, { ch: mu_plus, add: 1 }, { ch: gamma, add: 1 }]
phase: { gamma: "fixed:2" }
```

## Phase Assignment Keywords

| Keyword        | Meaning |
|----------------|---------|
| `inherit`      | Copy phase of matched incoming channel (unique match required). |
| `inherit_from:X`| Copy phase from specified channel. |
| `delta`        | Use local propagation phase shift from emitting edge. |
| `fixed:N`      | Assign phase index N mod k. |

## Deterministic Application Order
- All propagation for a layer occurs first.
- Coupling rules evaluate **once per layer**, in listed order.
- Inputs consumed by a rule **cannot** be reused in the same layer.

This ensures deterministic evolution.
