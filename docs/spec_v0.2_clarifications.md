# IRREPnet v0.2 Clarifications (Deterministic Coupling & Scope)

## Coupling Rule Execution Order
- Coupling occurs **after** propagation, masking, and accumulation for the current DAG layer.
- For each node touched in this layer, build a **working inventory** `W[ch,phase]` from inbound contributions that arrived **this layer** (`counts_next`).
- Maintain a separate **emission buffer** `Q[ch,phase]` for rule outputs.
- Process coupling rules **in YAML order**. Each rule fires **once**, with **multiplicity**:
  - For inputs `[{ ch: X, min: a }]`, compute maximum multiplicity:  
    `m = min( floor(W[X] / a) )` across required channels (phase handling below).
  - **Consume** `m * a` from `W` (removing used counts).
  - **Produce** `m * add` into `Q` (not back into `W`).
- **No rule chaining in the same tick:** Outputs in `Q` do **not** feed into other rules in this layer.
- On tick completion, `Q` becomes part of the next propagation step.

## Scope Semantics (Tags & Targeted Emission)
- Nodes and edges may declare `tags: [ ... ]` in topology:
  ```yaml
  nodes:
    - { id: 2, tags: ["scatter_zone"] }
  edges:
    - { id: 5, u: 2, v: 3, tags: ["positronium"] }
  ```
- Rule scoping:
  - `scope.nodes_any: ["tagA","tagB"]` → rule fires **only** on nodes with these tags.
  - `scope.out_edges_any: ["tagC"]` → rule outputs **only** to matching outgoing directed edges.
- If no `out_edges_*` is given → **broadcast** to all outgoing edges.
- Directed edges inherit tags from their `edge_ref` unless overridden.

## Phase Keywords During Coupling
For each **outgoing directed edge** receiving an emitted packet:
- `delta` → Use the propagation shift for that edge:  
  `(gauge[node] - gauge[nbr] + edge_offset[e]) mod k`
- `inherit` → Use the consumed input bundle's phase. Specify source if necessary:
  ```yaml
  phase: { gamma: "inherit_from:e_minus" }
  ```
- `sum` → Add listed input phases mod k:
  ```yaml
  phase: { gamma: { sum_from: [e_minus, e_plus] } }
  ```
- `fixed:p` → Assign constant phase `p`.

## Charge Conservation
- Default: rule must satisfy  
  `sum_in(q[ch]*min) == sum_out(q[ch]*add)` (times multiplicity).
- If intentionally violated, set:
  ```yaml
  nonconservative: true
  ```
- Engine automatically handles consumption and production; user does **not** specify explicit removal.

## Coupling Input Bookkeeping
- Counts in `W` are **single‑use** per layer. Once consumed by a rule, they are **not** available to later rules in that layer.
- Multiplicity allows a rule to fire the maximum number of whole times deterministically.

## Measurement Channel Filters
- If `channels` specified → **sum across those channels first**, then apply roots‑of‑unity over phases.
- If omitted → sum across **all channels** first.

## Migration (v0.1 → v0.2)
- Insert implicit neutral channel:
  ```yaml
  channels:
    - { name: default, charge: 0, neutral: true }
  ```
- Expand `[E,k] → [E,1,k]`.
- Expand any v0.1 fusion mask `[E,k] → [E,1,k]` unchanged.
- Measurement without channel specification behaves exactly as in v0.1.

## Summary Principle
- **W** holds inbound counts and is consumed during rule firing.
- **Q** holds emitted counts and does **not** feed back into coupling until the next tick.
- Determinism arises from: single-pass YAML-ordered rule execution, single-use inventory, and explicit multiplicity.

