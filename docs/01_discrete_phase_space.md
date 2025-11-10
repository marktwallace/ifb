# Discrete Phase Propagation in IFB
Version: v0.2

## 1. Why Zₖ Instead of ℂ

Quantum theory typically represents states as complex amplitudes.  
But if spacetime and geometry are *emergent*, the complex numbers are **not primitive**.

We replace:
- `exp(iθ)` → **k-phase index** in **Zₖ**
- amplitude interference → **integer count folding mod k**
- continuous unitary dynamics → **discrete phase propagation**

This retains the *structure of interference*, without:
- Hilbert spaces
- Norms
- Continuous derivatives

It is **explicitly computable** and runs efficiently on GPUs.

## 2. Representation

Each excitation is represented as:

\[
(\text{channel}, \phi), \quad \phi \in \mathbb{Z}_k
\]

The state is:

\[
\text{counts}[e, c, \phi] \in \mathbb{N}
\]

Meaning:  
“How many excitations of channel \(c\) with phase \(\phi\) exist along directed edge \(e\)?”

## 3. Propagation Rule

For each active directed edge:

\[
\phi' = (\phi + \delta_e + \text{gauge}(u) - \text{gauge}(v)) \mod k
\]

## 4. Why Gauge Matters

Only *relative* phase has meaning.

## 5. Fusion Masks and Phase Traps

Allowed-phase subsets define **quantized orbitals**.

## 6. Interference at Junctions

Phases combine at nodes; constructive/destructive outcomes emerge without amplitudes.

## 7. Interference Patterns Are Emergent Probability Distributions

Observable distributions arise from aggregated counts across phase.

## 8. Key Insight

Geometry emerges from correlation stability and propagation topology.
