# Simulation Design Specification (GPU-Oriented)

## Purpose

Define the recommended architecture for scalable, deterministic simulations of particle interaction graphs, optimized for PyTorch execution on GPUs.

The simulation models local interactions between particles (e⁻, μ⁺, γ) through discrete, rule-based updates applied to a graph of nodes and edges. The design emphasizes reproducibility, scalability, and emergent behavior arising from simple local rules.

## Design Principles

1. **Clarity and Determinism**
   - All random behavior derives from a seeded pseudo-random number generator (PRNG).
   - Each experiment is fully reproducible from its YAML configuration and PRNG seed.

2. **Division of Responsibilities**
   - **YAML configuration** specifies experiment parameters only:
     - Random seed
     - Graph size and degree
     - Phase group size (Zₖ)
     - Initial particle densities
     - List of active rules
     - Measurement selections
   - **Python implementation** defines all computational logic:
     - Graph generation
     - Rule execution
     - PRNG setup and deterministic sequencing
     - Measurements and outputs

3. **Core Abstractions**
   - **Graph**: Represented as tensors suitable for GPU operations.
     - `edge_index (2, E)` or CSR form (`rowptr`, `colidx`)
     - Boolean masks for tagged nodes/edges (e.g., muon sites, gamma edges)
   - **State**: Tensorized particle fields.
     - Example: `counts[edge, channel, phase]`
     - Optional auxiliary fields: `ttl[edge]`, `phase_offset[edge]`
   - **Rule**: Pure tensor function that transforms state via local operations.
     - Must use only PyTorch tensor operations (`index_select`, `gather`, `scatter_add_`, etc.)
     - No Python loops or branching inside rule functions.
   - **RuleSet**: Ordered container of rule modules.
     - Implements a simple `.forward(state, graph, gen)` interface.
     - Applies each rule sequentially using the same RNG.
   - **Simulator**: Manages iteration and measurement scheduling.

4. **GPU Execution Strategy**
   - Use `torch.Generator` for deterministic PRNG on the GPU.
   - Precompute random tensors for reproducibility and speed.
   - Use `torch.compile` (PyTorch 2.x) for kernel fusion and automatic graph optimization.
   - Minimize host-device synchronization by keeping the entire step on GPU.

5. **Minimal Rule Set**
   - `ScatterOneHop`: conservative random hop + phase kick
   - `BindEmitGamma`: e⁻ + μ⁺ → bound + γ emission
   - `UnbindAbsorbGamma`: γ absorption → unbind
   - `GammaWalk`: γ propagation with TTL decay

6. **Scalability Goal**
   - Single unified code path runs for systems from 10 to 10⁶ atoms.
   - Performance scales with GPU memory and tensor parallelism.
   - Deterministic runs across CPU and GPU with identical seeds.

7. **Measurement Framework**
   - Measurements implemented as tensor reductions and statistics:
     - Pair correlations
     - Mean free path
     - Spectral dimension estimates
     - Backbone current and time-of-flight histograms

## Summary

This design ensures that all physical logic resides in fast, vectorized PyTorch code, while YAML remains a lightweight experiment descriptor. The approach supports reproducible large-scale simulations and provides a clean foundation for testing emergent behavior in muonium clouds or related systems.
