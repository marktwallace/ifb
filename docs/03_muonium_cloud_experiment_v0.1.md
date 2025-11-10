# Muonium Cloud Experiment — v0.1
Project: IFB — Engine: `irrepnet`

## Purpose
This experiment demonstrates how **phase-trapped positronium-like loops** and **muonium-like loops** interact with a traversing electron stream, producing gamma emissions whose distribution encodes **interference and emergent correlation geometry**.

## Topology Summary

```
corridor: 0 → 1 → 2 → 4 → 5
positronium loop: 2 ↔ 3
muonium loop:     2 ↔ 7
gamma line:       2 → 6
```

Node 2 is the **scatter zone** where bremsstrahlung and loop transitions occur.

## Initialization

```
counts_init:
  - { edge: 0, channel: e_minus, phase: 0, value: 200 }
```

This is a **directed electron beam injection**.

## Key Observables

| Name | Edges | Meaning |
|------|-------|---------|
| gamma_out_R   | [8]  | Gamma emissions detected to the right (primary signal). |
| electron_R    | [6]  | Transmitted electron flux. |
| loop_positron | [11] | Population trapped in positronium loop. |
| loop_mu_plus  | [13] | Population trapped in muonium loop. |

## Expected Behavior Patterns

1. **Gamma emission** increases when incoming e⁻ repeatedly encounters bound loops.
2. Positronium and muonium loops act as **phase filters**, creating distinct gamma phase signatures.
3. **Interference** appears in the gamma_out_R measurement as periodic modulation when gauge_phase at nodes is varied.

## Interpreting Emergent Geometry

No coordinates exist — geometry is inferred through correlations:

- Stable loop-trapped populations indicate **localized bounded regions**.
- Transmission vs capture patterns indicate **effective scattering lengths**.
- Gamma emission angular distribution (once generalized to multi-branch corridors) produces **radial-like cloud envelopes**.

In repeated forward/backward corridor topologies, geometry appears when:
- correlation neighborhoods become **statistically smooth under coarse-graining**.

This is the core phenomenon to analyze in the notebook.
