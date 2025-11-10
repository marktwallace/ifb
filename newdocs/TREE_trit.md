
# TREE.md — Project Structure (Trit Core)

## Tensor Conventions

| Symbol            | Shape   | Meaning                                      |
|-------------------|---------|----------------------------------------------|
| `signed_counts`   | [E, C]  | net signed flux per edge & channel           |
| `abs_counts`      | [E, C]  | optional absolute counts for diagnostics     |
| `ttl_gamma`       | [E]     | gamma lifetime per edge                      |
| `edge_tag`        | [E]     | optional tiny group element for holonomy     |
| `rowptr,colidx`   | CSR     | adjacency                                    |
| `edge_src,dst`    | [E]     | endpoint indices                             |

**Channels:** `{e⁻:0, μ⁺:1, e⁺:2, γ:3}`

## Canonical rule order per tick
1. `scatter_onehop`
2. `gamma_walk_ttl`
3. `bind_emit_gamma`
4. `unbind_absorb_gamma`

## Config (YAML)
```
seed, N, degree, gamma_ttl, densities, enable, measure, ticks, arrival_mod_k, holonomy_group
```

## Tests
- `test_determinism.py`
- `test_conservation.py`
- `test_invariants.py`
- `test_holonomy.py`
- `test_arrival_mod_k.py`
