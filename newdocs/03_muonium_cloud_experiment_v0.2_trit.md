
# Muonium Cloud Experiment — v0.2 (Phase‑Free Trit Core)

## Purpose
Demonstrate diffusion, light‑cone‑like fronts, and interference‑like cancellations **without stored phases**, using signed tokens, arrival‑mod‑k detectors, and optional holonomy.

## Topology (example)
```
corridor: 0 → 1 → 2 → 4 → 5
muonium loop: 2 ↔ 7
gamma line:  2 → 6
detectors:   D_R on edge(2→6), D_T on edge(4→5)
```

## Initialization
```
signed_counts_init:
  - { edge: 0, channel: e_minus, value: +200 }   # pulsed source over T ticks
gamma_ttl: 6
arrival_mod_k: 8
```

## Observables
- `ToF_D_R` (first‑arrival ticks at D_R)
- `MSD` from spreading along corridor
- `ArrivalModK_D_R` (histogram of `(arrival_tick mod k)`)
- `HolonomyDiff` (optional): compare D_R vs an alternate path enclosing a tagged loop

## Expected Patterns
1. Expanding front in ToF; MSD ~ t^α (α near 1 for random walk).
2. Stable fringes in `ArrivalModK_D_R` if multiple path families compete.
3. Signal differences when loop tagging is enabled (holonomy).

## Stretch Goal
Constrain the muonium loop so that signed flux exhibits discrete trapping levels detectable as persistent population plateaus (hydrogenic‑like hints).
