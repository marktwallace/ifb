
# Sign Dynamics — From Interference to Holonomy (Phase‑Free)

## 1. Token Semantics
A token is `(channel, sign)`, where `sign ∈ {+1, −1}`. Creation and annihilation events must preserve relevant invariants (e.g., lepton number per channel where appropriate).

## 2. Three Mechanisms for Phase‑Like Emergence

### A. Orientation/Parity Signs
Define a small set of **graph motifs** (e.g., left‑turn vs right‑turn at degree‑3 nodes). Assign a parity `p ∈ {+1, −1}` to motif traversals. When a token traverses the motif, multiply its sign by `p`. Summed signals at detectors show cancellations if competing families of paths differ in parity count.

### B. Clock‑from‑Distance
Detectors keep `(arrival_tick mod k)` bins (k small, e.g., 8 or 16). Emission is pulsed. Pure path‑length differences produce fringe‑like patterns in the modulo histogram — without any per‑token phase memory.

### C. Discrete Holonomy (Loop Tags)
Maintain a tiny edge tag group `G` (Z2 or Z4). Rules can toggle tags at events. A token crossing an edge applies `sign *= χ(tag)`, where `χ` is a fixed character `G → {±1}`. Different loops yield different net sign products → holonomy. Tags are stateful but **emerge** from dynamics (not fixed at input).

## 3. Tensor Formulation

- `signed_counts[E, C]` (int32/64) updated by scatter‑adds.  
- Optional `edge_tag[E]` in `{0..|G|-1}`; lookup `sign_flip = table[edge_tag]` as a vectorized gather.  
- Motif parity uses precomputed index lists for affected edges; apply batched sign flips with masking.

## 4. Tests

- **Parity cancellation test:** two equal‑length corridors with opposite motif parities → near‑zero net signal.
- **Holonomy test:** two detector paths enclosing different tagged cycles → distinct signals.
- **Clock test:** periodic source; check stable fringes in arrival‑mod‑k histograms.

## 5. Failure Modes

- If all three mechanisms fail to produce structure, re‑introduce a **minimal** internal tag alphabet (still finite) or reconsider rule richness / topology.
