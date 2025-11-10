# TREE.md — Project Structure and Conventions

This document defines the directory layout, naming conventions, and key architectural guidelines for the clean‑slate implementation of the muonium cloud simulation. It is intentionally concise and forward‑looking, serving as the project’s root design map.

---

## Directory Layout

```
.
├── README.md                       # Overview and quick start
├── docs/
│   ├── 03_muonium_cloud_experiment_v0.2.md
│   ├── 04_simulation_design.md
│   └── TREE.md                     # (this file)
├── ifb/                            # Core Python package
│   ├── __init__.py
│   ├── config.py                   # Load + validate YAML
│   ├── graph.py                    # Seeded graph generator (CSR tensors)
│   ├── state.py                    # Allocate + manage tensors for counts/phases
│   ├── rng.py                      # Deterministic PRNG (torch.Generator)
│   ├── sim.py                      # Simulator + rule sequencer (torch.compile)
│   ├── measure.py                  # GPU‑based measurements
│   └── rules/
│       ├── __init__.py
│       ├── scatter_onehop.py
│       ├── bind_emit_gamma.py
│       ├── unbind_absorb_gamma.py
│       └── gamma_walk_ttl.py
├── experiments/
│   ├── cloud_10.yaml
│   ├── cloud_100.yaml
│   ├── cloud_1000.yaml
│   └── cloud_10000.yaml
├── tests/
│   ├── test_determinism.py
│   ├── test_conservation.py
│   └── test_invariants.py
└── scripts/
    ├── run.py                      # Run a single experiment
    ├── sweep.py                    # Parameter sweeps (N, seeds)
    └── plot.py                     # Quick analysis / visualization
```

---

## Tensor Conventions

| Symbol | Shape | Meaning |
|--------|--------|---------|
| `counts` | `[E, C, K]` | particle counts per edge, channel, phase |
| `phase`  | `[E, C]` | current phase index for each channel |
| `ttl`    | `[E]` | photon lifetime counter |
| `rowptr`, `colidx` | CSR graph adjacency |
| `edge_src` | `[E]` | source node index for each edge |

**Channels:** `{e⁻:0, μ⁺:1, γ:2}`  
**Phase group:** integers mod‑K (Zₖ)

---

## Rule Design

- Each rule is a **pure torch function**: `(state, graph, gen) → state`
- Use tensor operations only (`index_select`, `gather`, `scatter_add_`, etc.)
- No Python loops inside kernels.
- Each rule file should contain:
  - A short docstring describing its purpose and invariants.
  - A single `forward()` or `apply()` entry point.
  - Optional helper functions limited to local tensor ops.

**Canonical rule sequence per tick:**
1. `scatter_onehop`
2. `gamma_walk_ttl`
3. `bind_emit_gamma`
4. `unbind_absorb_gamma`

---

## Determinism and Reproducibility

- Single `torch.Generator(device)` seeded from YAML.  
- All randomness (edge selection, phase kick) comes from this generator.  
- No CPU RNG or numpy RNG use allowed.  
- Same seed ⇒ identical output bitwise (across CPU/GPU within tolerance).

---

## Config and Experiment Flow

- YAML defines: `{seed, N, degree, K, gamma_ttl, densities, enable, measure, ticks}`
- Python parses config → builds graph/state → runs simulation.  
- Output = JSON lines of measurement summaries + config hash.

---

## Tests and Invariants

| Test | Purpose |
|------|----------|
| `test_determinism` | same seed → identical result |
| `test_conservation` | total charge conserved each tick |
| `test_invariants` | non‑negative counts, TTL ≥ 0, no cloning |

---

## Performance Roadmap

1. **CPU Torch first**, verify correctness.  
2. **Enable GPU**, use `torch.compile(fullgraph=True)`.  
3. Profile; precompute RNG tensors.  
4. Maintain constant memory footprint for 10 → 10⁶ atom scaling.

---

## Developer Notes

- Each rule ≤150 LOC, single responsibility.  
- Avoid unnecessary domain metaphors in code; prefer simple verbs (`bind`, `unbind`, `scatter`, `walk`).  
- Keep all math explanations and physics rationale in `docs/`, not embedded in code comments.  
- Maintain strict separation of configuration, simulation, and measurement layers.

---

## Optional Future Enhancements

- Lightweight visualizer for photon and charge density over the graph.  
- Checkpointing for long runs.  
- Golden outputs for CI consistency.

---

**End of TREE.md**
