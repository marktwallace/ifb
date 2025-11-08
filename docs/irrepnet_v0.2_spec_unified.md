# IRREPnet v0.2 — Unified Spec (Multi‑Channel Edges, Deterministic Coupling, Tags & Scope)

**Status:** Stable (implementation target)**  
**Goal:** Extend v0.1 to support multiple species/channels, node‑local deterministic coupling rules, and tag‑based scoping — while preserving integer‑only evolution, mod‑k phase algebra, and gauge invariance.

---

## 0. Invariants (must remain true)

1. **Integer‑only evolution.** `counts` stays `int32` during propagation and coupling. Floats/complex appear **only** in measurement.
2. **Phase algebra mod k.** All phase arithmetic uses non‑negative integer math modulo `k`.
3. **Gauge invariance.** Uniform shift of all node `gauge_phase` leaves measurements unchanged. Charged channels transform; neutral channels do not.
4. **Fusion mask is a veto.** `0` = forbidden, `1` = allowed. No soft weights or epsilons.
5. **Layer isolation.** No directed edge appears twice in a single DAG layer. Double‑buffering prevents read/write conflicts.
6. **No implicit normalization.** Never rescale or renormalize counts during evolution.
7. **Deterministic updates.** No stochasticity in v0.2; rules fire with maximal multiplicity once per layer in YAML order (see §3.5).

---

## 1. Data model

### 1.1 Phase group
```yaml
phase_group: { kind: "Zk", k: 8 }
```
- All phase operations are performed modulo `k`.

### 1.2 Topology (tags are allowed)
```yaml
nodes:
  - { id: 0, label: "src_L",  irrep_code: 0, gauge_phase: 0, tags: ["inlet"] }
  - { id: 1, label: "mid_1",  irrep_code: 0, gauge_phase: 0 }
  # ...

edges:           # undirected edge refs (expand to two directed edges unless sym:false)
  - { id: 0, u: 0, v: 1, sym: true,  phase_offset: 0, tags: ["corridor"] }
  - { id: 1, u: 1, v: 2, sym: true,  phase_offset: 0 }
  # ...
```
> **Tags:** Both `nodes` and `edges` may include optional `tags: [..]`. These tags are used by rule `scope` to restrict where rules fire and/or where they emit.

### 1.3 Directed edges
```yaml
directed_edges:
  - { id: 0, src: 0, dst: 1, edge_ref: 0, enabled: true }
  - { id: 1, src: 1, dst: 0, edge_ref: 0, enabled: true }
  # ...
```
- `edge_ref` points back to the undirected edge. Directed edges inherit `tags` from their `edge_ref` unless overridden with their own `tags` field.

### 1.4 Channels
```yaml
channels:
  - { name: e_minus,  charge: -1, neutral: false }
  - { name: e_plus,   charge: +1, neutral: false }
  - { name: mu_plus,  charge: +1, neutral: false }
  - { name: gamma,    charge:  0, neutral: true  }
```
- Loader assigns channel indices `0..C-1` in order. `neutral:true` → no gauge term during propagation (see §3.2).

### 1.5 Runtime tensors (shapes)
- **Counts:** `counts : int32 [E, C, k]` — counts per directed edge × channel × phase.
- **Fusion mask:** `fusion_mask : uint8 [E, C, k]` or sparse (see §2.2).
- **Gauge phases:** `gauge : uint8 [V]` — node‑local references (applies only to charged channels).
- **Edge offsets:** `edge_offset : uint8 [E]` — per directed edge (via `edge_ref` or specified directly).

---

## 2. Scenario file schema

### 2.1 Required fields
```yaml
irrepnet_dm: "0.2"
phase_group: { kind: "Zk", k: <int> }
nodes: [ ... ]            # may include tags
edges: [ ... ]            # may include tags
directed_edges: [ ... ]   # optional tags; inherit from edge_ref by default
channels: [ ... ]
dag:                      # layer schedule (see v0.1)
measurement: { ... }      # roots_of_unity readout (see §4)
```

### 2.2 Fusion mask (choose exactly one form)
**Dense:**
```yaml
fusion_mask:  # shape [E][C][k], 0/1
  - - [ ... k bits for channel 0 on edge 0 ... ]
    - [ ... k bits for channel 1 on edge 0 ... ]
  # ...
```

**Sparse:**
```yaml
fusion_mask_sparse:
  - { edge_id: 0, channel: e_minus, allow_phases: [0,4] }
  - { edge_id: 0, channel: gamma,   allow_phases: [0,1,2,3,4,5,6,7] }
```
- Loader expands to one‑hot mask for those `(edge, channel, phase)` entries.  
- If both dense and sparse are present, loader raises `E_FUSION_MASK_CONFLICT`.

### 2.3 Counts initialization
```yaml
counts_init:
  - { edge: 0, channel: e_minus, phase: 0, value: 200 }
```

### 2.4 Coupling rules (node‑local, deterministic)
**Where:** After propagation, masking, and accumulation for the current layer, rules fire **per node** touched in this layer.

**Scope (final syntax):**
```yaml
scope:
  nodes_any: ["tagA","tagB"]      # rule may fire only on nodes with any of these tags
  out_edges_any: ["tagC","tagD"]  # rule emits only to outgoing directed edges with any of these tags
```
- If `nodes_any` is omitted → can fire on any node.
- If `out_edges_any` is omitted → **broadcast** outputs to all outgoing edges of the node.
- Directed edges inherit tags from `edge_ref` unless they define their own.

**Rule schema:**
```yaml
coupling_rules:
  - name: brems_emit
    scope: { nodes_any: ["scatter_zone"], out_edges_any: ["gamma_line"] }
    in:   [{ ch: e_minus, min: 1 }]
    out:  [{ ch: e_minus, add: 1 }, { ch: gamma, add: 1 }]
    phase:
      e_minus: "inherit"                 # see defaults below
      gamma:  "delta"                    # per-recipient edge Δ (see §3.3)
```
- Inputs may carry `sum_over_phases: true` to pool phase bins before computing multiplicity.

**Execution (per node) — deterministic:**
1. Build **working inventory** `W[ch,phase]` from inbound contributions that arrived **this layer** (`counts_next`).
2. Maintain separate **emission buffer** `Q[ch,phase]` for rule outputs.
3. Process rules **in YAML order**, each **once** with **maximal multiplicity** `m`:
   - For each input `{ch, min=a}` compute how many whole times it can fire given `W` (respecting `sum_over_phases` if set).
   - **Consume** `m*a` from `W` (single‑use within the layer).
   - **Produce** `m*add` into `Q` (does **not** feed back into `W` this layer).
4. After all rules on that node: distribute `Q` to recipient outgoing edges (respecting `scope.out_edges_any`).

**No rule chaining within the same layer.** New outputs influence later layers/ticks only.

---

## 3. Evolution semantics

### 3.1 Per layer
1. Select directed edges `I` in the layer.
2. **Propagate** `counts[I,:,:]` with per‑channel phase law (below).
3. **Apply fusion mask** (veto).
4. **Accumulate** to `counts_next` on destination nodes’ outgoing edges.
5. **Couple** per node deterministically (as in §2.4).  
6. Swap buffers; advance to next layer. Repeat per `dag.repeat`.

### 3.2 Phase law per channel
For a directed edge `e: src→dst` and channel `c`:
- **Charged channel:**  
  `Δ = (gauge[src] - gauge[dst] + edge_offset[e]) % k`  
  Shift counts over phase by `+Δ` (circular roll).
- **Neutral channel:**  
  `Δ = edge_offset[e] % k` (no gauge term).

### 3.3 Phase assignment in coupling outputs
For each emitted packet to a recipient outgoing edge `e: node→nbr`:
- `delta` → use the local propagation shift for **that recipient edge**:  
  `Δ_e = (gauge[node] - gauge[nbr] + edge_offset[e]) % k` (or just `edge_offset[e]` if neutral channel).
- `inherit` → copy the consumed input’s phase.
  - **Default:** if the rule has **exactly one** input channel, `"inherit"` is unambiguous.  
  - **Otherwise:** require `"inherit_from:<channel_name>"`.
- `sum` → sum phases from listed inputs modulo `k`:  
  `phase: { gamma: { sum_from: [e_minus, e_plus] } }`
- `fixed:p` → constant phase `p ∈ [0..k-1]`.

### 3.4 Charge conservation
- Rules are **conservative by default** and must satisfy:  
  `Σ_in q[ch]*min == Σ_out q[ch]*add` (times multiplicity).
- To intentionally violate this (e.g., annihilation), set `nonconservative: true`. Runtime asserts accordingly.

### 3.5 Determinism checklist
- Single pass over rules **in YAML order**.
- Single‑use inputs: consumption removes counts from `W` for the current layer.
- Outputs do not chain within the layer (go to `Q` and onward next tick).
- No RNG; integer arithmetic only.

---

## 4. Measurement (roots of unity)

```yaml
measurement:
  representation: "roots_of_unity"
  outputs:
    - { name: "gamma_out_R", readout_edges: [8],  channels: [gamma] }
    - { name: "lepton_R",    readout_edges: [6],  channels: [e_minus,e_plus] }
    - { name: "all_right",   readout_edges: [6,8] }  # no channels → sum all channels
```
- If `channels` is specified: **sum counts over those channels first**, then project over phase with roots of unity, then return squared magnitude.
- If `channels` is omitted: **sum across all channels first**, then project.

---

## 5. Migration from v0.1

- Accept `irrepnet_dm: "0.1"` and **lift** to v0.2 by inserting a single neutral channel:
  ```yaml
  channels: [{ name: default, charge: 0, neutral: true }]
  ```
- Expand shapes `[E,k] → [E,1,k]`.
- Expand any v0.1 fusion mask `[E,k] → [E,1,k]` unchanged.
- Measurement without channel filters behaves identically to v0.1 (sum then project).

---

## 6. Tests (must pass)

1. **Shape sanity:** `counts` `[E,C,k]`, `fusion_mask` shape matches.
2. **Gauge invariance:** uniform gauge shift leaves measurements unchanged for charged‑only selections; neutrals ignore gauge.
3. **Two‑path interference:** reproduce v0.1 per charged channel.
4. **Neutral propagation:** responds to `edge_offset` only.
5. **Bremsstrahlung rule:** increases `gamma` and conserves charge.
6. **Determinism:** repeated runs from reset are identical.
7. **Mask veto:** zero mask ⇒ zero measurement.
8. **Charge conservation assertions:** conservative rules pass per‑tick checks.

---

## 7. Implementation checklist (loader & sim)

- **loader.py**
  - Parse `channels` and build `name→index`, `charge[]`, `neutral[]`.
  - Parse `fusion_mask` dense or sparse; expand to `[E,C,k]` `uint8`.
  - Support `tags` on `nodes`, `edges`, and optional `directed_edges`.
  - Validate DAG (no repeated edges in a layer).
  - Lift v0.1 → v0.2 as described.

- **sim.py**
  - Buffers: `counts:int32[E,C,k]`, `counts_next` same.
  - Propagation: per‑channel phase roll (charged vs neutral).
  - Apply fusion mask; accumulate to `counts_next` via precomputed `(T,R)` indices per layer.
  - Node‑local coupling: build `W` from arrivals; process rules in order with multiplicity; fill `Q`; distribute to recipients (scoped).

- **measure.py**
  - Add optional `channels` filter in readout.

- **scripts/**
  - Update tools to accept `--channel` where appropriate.

---

## 8. Guiding principle

> We evolve **discrete correlation counts** over a tagged graph with mod‑k bookkeeping.  
> The only continuous object is the **phasor at readout**.  
> Interference, gauge invariance, and (in later versions) entanglement emerge from **combinatorial structure**, not from continuous wavefunctions.
