# IRREPnet Cursor Briefing (Development Guardrails)

This document is for GPT-5 in Cursor. It encodes the **non-negotiable invariants** and safe implementation patterns.

---

## Core Invariants (Must Not Drift)

| Rule | Meaning |
|---|---|
| **Integer-only evolution** | `counts` is `int32`; no floats during propagation. |
| **Phase algebra is mod k** | Represent phases as unsigned integers; compute with `% k`. |
| **Gauge invariance** | A uniform shift to all `gauge_phase[v]` must not change measurement. |
| **Fusion mask is a veto** | `fusion_mask[e,g] == 0` means `(e,g)` contributes **zero**. |
| **DAG layers do not re-enter** | No directed edge appears twice in a layer; use double-buffering. |
| **No normalization** | Do not rescale `counts` as system evolves. |

---

## Pitfalls to Avoid

- Converting to float inside update loops.
- Using negative indices for phase math (always `(x % k)`).
- In-place modification of tensor views that breaks broadcast.
- Implicit normalization or probability interpretation during evolution.

If something looks like a standard wavefunction simulation, **the code has gone off-track.**

---

## Phase-Safe Arithmetic Pattern

```python
# Compute rotation Δ = (gauge[src] - gauge[dst] + edge_offset) % k
delta = (phase_src - phase_dst + phase_offset) % k

# Circular shift of counts
shifted = counts_e.roll(shifts=int(delta), dims=0)

# Apply fusion mask (0 = veto, 1 = allowed)
allowed = shifted * fusion_mask[e]
```

No floats here.

---

## Layer Accumulation Pattern (Vectorized Safe Form)

```python
e_idx = torch.tensor(edges_in_layer, dtype=torch.long, device=device)
dst_sel = dst[e_idx]        # [E]

allowed = allowed  # shape: [E, k]

targets = []
row_ids = []
for row, v in enumerate(dst_sel.tolist()):
    targets.extend(out_index[v])
    row_ids.extend([row] * len(out_index[v]))

if targets:
    T = torch.tensor(targets, dtype=torch.long, device=device)  # [F]
    R = torch.tensor(row_ids, dtype=torch.long, device=device)  # [F]
    counts_next.index_add_(0, T, allowed.index_select(0, R))    # integer accumulation
```

This is correct, safe, deterministic, and ready for later optimization.

---

## Measurement (Only Place Where Floats Are Allowed)

```python
n_g = counts[e, :]  # sum phases per edge-set
A = (n_g * exp(2πi * g / k)).sum()
P = |A|^2
```

Use **complex64 or complex128**.

---

## Tests Required to Confirm Correctness

| Test | Expected Outcome |
|---|---|
| Triangle uniform gauge shift | Measurement unchanged |
| Fusion mask zeroed | All outputs zero |
| Two-path gauge flip by k/2 | Constructive ↔ destructive swap |
| Determinism | Run twice from reset → identical counts |
| Export/Import state roundtrip | Values preserved |

---

## Loader Rules

- Accept **either** `fusion_mask` (dense) or `fusion_mask_sparse`, not both.
- Validate DAG: no repeated edges within a layer.
- Validate that all nodes and edges referenced exist.

---

## Performance Notes

- Keep everything integer until measure.
- Optimize accumulation only after correctness is locked.
- Precompute `(T, R)` lists per layer for speed.

---

## Motto

> **Do not let the code drift toward a wavefunction interpretation.**  
> We are evolving **discrete correlations**, not amplitudes.  
> The only continuous object is the phasor in measurement.

---

End of briefing.
