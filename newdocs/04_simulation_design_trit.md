
# Simulation Design Specification (Phase‑Free Trit Core)

## Purpose
Run scalable, deterministic simulations of local particle‑interaction graphs using **signed integer dynamics** (no phases).

## Abstractions
- **Graph:** CSR/COO tensors (`rowptr`, `colidx`, `edge_src`, `edge_dst`).
- **State:** `signed_counts[E, C]`, optional `abs_counts[E, C]`, `ttl_gamma[E]`, optional `edge_tag[E]`.
- **RuleSet:** ordered pure‑tensor modules `(state, graph, gen) → state`.
- **Simulator:** seeds `torch.Generator`, precomputes RNG tensors, uses `torch.compile`.

## Execution
- Keep full step on GPU; no host sync in inner loop.
- Deterministic PRNG: single `torch.Generator(device)` for all randomness.
- Measurements as tensor reductions: ToF maps, MSD, arrival‑mod‑k hist, holonomy differentials.

## Minimal Rule Set
1. `scatter_onehop`
2. `gamma_walk_ttl`
3. `bind_emit_gamma`
4. `unbind_absorb_gamma`

## Tests/Invariants
- Determinism (same seed → same bytes within tolerance)
- Conservation (non‑γ signed totals conserved per tick)
- Nonnegativity for diagnostics (`abs_counts ≥ 0`, `ttl ≥ 0`)
