# IFB Foundations — Core Objects and Semantics
Project: **IFB** — Simulator package: **`irrepnet`**  
Version: **v0.2 (stable ontology)**

## 1. Motivation

IFB models the world not from *space and time*, but from **information structure**:

- **Nodes** represent *irreducible excitation carriers* (“what can exist”).
- **Edges** represent *correlation* (“what is bound to what”).
- **Channels** represent *types of excitation* permitted to propagate along edges.
- **Phase** represents *internal relational state*, used to model interference.

There is **no metric**, **no coordinate system**, and **no background geometry**.  
Any notion resembling *space* or *distance* must *emerge* from the structure and evolution of correlations.

## 2. Nodes

A **node** is an abstract site where correlated excitations meet.

```
node:
  id: <int>
  label: <human name>
  gauge_phase: <integer mod k>
  tags: [optional semantic labels]
```

Nodes **do not have coordinates**.  
They do not “sit somewhere.” They only **connect**.

Nodes can carry *local gauge offsets* that affect phase composition along edges.

## 3. Edges

An **edge** indicates that nodes share a *correlation channel*.

Two layers:

1. **Undirected Edge** = “these two nodes are linked”
2. **Directed Edges** = “allowed propagation direction(s)”

```
edges:
  - { id: 4, u: 2, v: 6, sym: true, tags: ["gamma_line"] }

directed_edges:
  - { id: 8, src: 2, dst: 6, edge_ref: 4, enabled: true }
  - { id: 9, src: 6, dst: 2, edge_ref: 4, enabled: true }
```

**Important:**  
Edges do **not** have geometry.  
Geometry is what we infer from the **structure of correlations** that form and persist.

## 4. Channels (What Propagates)

A **channel** is the *type* of excitation:

```
channels:
  - { name: e_minus, charge: -1, neutral: false }
  - { name: gamma,   charge:  0, neutral: true  }
```

Channels are **fundamental** (in v0.2) — **they are irreps**.

There is one way to be an electron.  
There is one way to be a photon.  
There is no internal structure *below* channels.

This is the **irreducibility constraint**:
> Physics is built from *irreps*, not arbitrary composites.

## 5. Phase (Internal Relational State)

Every count of a channel traveling along an edge carries a **phase**:

- Domain is **Z_k** (a finite cyclic group).
- Used to model interference without continuous amplitudes.

Propagation applies local transformations:
\[
\phi' = (\phi + \text{edge\_offset} + \text{gauge}(u) - \text{gauge}(v)) \mod k
\]

There are **no complex wavefunctions here**.  
All “wave-like” behavior comes from:

- phase propagation along multi-step paths
- interference at junctions (nodes)
- channel-constrained recombination rules

## 6. Counts, Not Amplitudes

Instead of storing amplitudes, we store **counts indexed by phase**:

```
counts[edge, channel, phase] = integer ≥ 0
```

Interference happens when multiple paths accumulate contributions with phases that either:

- produce **constructive alignment** (counts reinforce), or
- **cancel mod k** (counts fail to reinforce and effectively disappear in measurement).

No floating point amplitudes → **fully finite / discrete** → GPU/TPU-friendly.

## 7. Coupling Rules (Local Updating Dynamics)

Coupling rules define how excitations interact at nodes:

```
in:
  - { ch: e_minus, min: 1 }
  - { ch: mu_plus, min: 1 }
out:
  - { ch: e_minus, add: 1 }
  - { ch: mu_plus, add: 1 }
  - { ch: gamma,   add: 1 }
phase:
  gamma: "fixed:2"
```

Interpretation:

- If a node receives an **electron** and a **muon+**,  
- the system emits **a gamma** with discrete phase = 2,
- while preserving conservation and channel identity.

Rules are **local**, deterministic, and do not depend on global state.

## 8. Measurement

Final readouts compute aggregated observables:

- Sum counts across phase → population measurement
- Convert phase distribution → interference pattern
- Compute temporal evolution → “arrival profile”
- Project structure → inferred *geometry*

There is **no external detector space**.  
If something looks “far away,” that is because the **correlation graph evolved that way.**

## 9. What Emerges (The Goal)

If this structure is correct, then:

- **Position** is inferred from *relative stability of correlation neighborhoods*
- **Momentum** is inferred from *persistence of directed phase transport*
- **Energy levels** arise from *phase trapping under fusion constraints*
- **Geometry** emerges from *stable long-range correlation topology*

No continuity required.  
No background spacetime input.  
Everything is **relational information**.
