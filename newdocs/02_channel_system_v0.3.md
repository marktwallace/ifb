
# Channel System Specification — v0.3 (Phase‑Free Trit Core)
Project: IFB — Engine: `irrepnet`

## Channels
```
e_minus (−1 charge), e_plus (+1), mu_plus (+1), gamma (0)
```
Channels are irreps; there is one way to be each particle.

## State
```
signed_counts[edge, channel] ∈ ℤ
ttl_gamma[edge] ∈ ℕ0
edge_tag[edge] ∈ G (optional small finite group, e.g., Z2)
```

## Local Rules (Illustrative)

### ScatterOneHop
- Move a fraction of `signed_counts` along one‑hop out‑edges (deterministic or RNG‑split) using a seeded generator.
- Apply optional **parity flip** based on precomputed motif masks.

### BindEmitGamma (muonium‑like transition)
- If e⁻ meets μ⁺ at a node, re‑emit e⁻ and μ⁺ on outgoing edges and **create γ** on designated γ edges.
- Preserve net signed totals for non‑γ channels.
- Optionally toggle an `edge_tag` on the γ edge (holonomy seed).

### UnbindAbsorbGamma
- Absorb γ when meeting a compatible loop/site; increment signed e⁻ or μ⁺ as needed (conservative bookkeeping).

### GammaWalkTTL
- γ propagates randomly or deterministically with `ttl--`; when `ttl == 0`, remove γ contribution.

All rules are tensorized; no Python loops inside kernels.
