
# IFB Foundations — Trit Core (Phase‑Free)
Project: **IFB** — Engine: **`irrepnet`**  
Version: **v0.3 (phase‑free trit ontology)**

## 1. Motivation

We remove built‑in phase and complex amplitudes. Dynamics are **purely discrete** and **sign‑based**:
- Local events add **signed contributions** (+1, −1) or no contribution (0).
- Observables emerge from **combinatorics, timing, and holonomy**, not from stored phases.

## 2. Core Objects

- **Nodes**: abstract interaction sites (no coordinates).
- **Edges (directed)**: possible propagation channels between nodes.
- **Channels**: irreps for particle types (e⁻, μ⁺, e⁺, γ). No internal structure below channels.
- **Tokens**: event quanta that carry **sign ∈ {−1, +1}** and a **channel**.

## 3. State Representation (Phase‑Free)

Instead of counts binned by phase, we store **signed integer flux** per directed edge and channel:

```
signed_counts[edge, channel] ∈ ℤ
abs_counts[edge, channel]    ∈ ℕ   # optional, for diagnostics
ttl_gamma[edge]              ∈ ℕ0   # optional, per‑edge TTL for γ propagation
edge_tag[edge]               ∈ G    # optional, tiny finite group for holonomy (e.g., Z2 or Z4)
```

Interpretation: `signed_counts` is the **net** effect of local token creation/annihilation and transport during the last tick (or cumulatively, depending on the measurement window).

## 4. Dynamics (Local, Conservative)

A **Rule** is a pure tensor function `(state, graph, gen) → state` with only local reads/writes:
- Token propagation: one hop along enabled directed edges.
- Interactions: local integer updates that respect invariants (e.g., charge conservation).  
- Optional **sign flips** on specific motifs (turns, junction orientation), enabling interference‑like cancellations **without amplitudes**.
- Optional updates to `edge_tag` to realize **discrete holonomy**; tags influence sign assignment when a cycle is traversed.

**No** Python loops; use tensor ops only.

## 5. Measurements (Emergent Geometry & “Phase‑Like” Effects)

- **First‑arrival maps / time‑of‑flight (ToF):** define null‑cone–like fronts by earliest tick of nonzero flux at detectors.
- **Diffusion scaling:** MSD vs ticks to estimate an effective metric/spectral dimension.
- **Arrival‑mod‑k histograms:** detectors bin events by `(arrival_tick mod k)` → fringe patterns purely from path‑length combinatorics (“clock‑from‑distance”).
- **Holonomy probes:** compare detector counts across path families that enclose different cycles; differences imply nontrivial loop tags.

## 6. Invariants & Consistency

- Integer arithmetic only (no floats).
- Exact conservation for signed totals per conserved quantum number (e.g., net charge of non‑γ channels).
- Non‑negativity checks for diagnostics (`abs_counts ≥ 0`, `ttl ≥ 0`).

## 7. What Should Emerge

- Apparent locality from stable correlation neighborhoods.
- Light‑cone–like fronts from ToF statistics.
- Interference‑like cancellations from sign rules and cycle holonomy.
- Hydrogenic‑like level hints only if loop constraints + sign rules create stable quantized trapping (stretch goal).

**Bottom line:** All “phase”‑looking phenomena arise from **timing, parity, or holonomy**, not stored phases.
