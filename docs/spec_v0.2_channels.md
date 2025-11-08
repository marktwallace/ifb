# IRREPnet v0.2 — Multi‑Channel Edges & Local Couplings
**Status:** Draft (implementation target)**

**Scope:** Extend v0.1 single‑channel simulator to support *multiple species/channels* per edge and *local coupling rules* at nodes, while preserving integer‑only evolution and gauge invariance.

---

## 0. Invariants (must remain true)
- **Integer‑only evolution.** `counts` tensor stays `int32` during propagation and coupling. Floats/complex appear **only** in measurement.
- **Phase algebra mod k.** All phase arithmetic is modulo `k` on non‑negative integer dtypes.
- **Gauge invariance.** Uniform shift of all node `gauge_phase` leaves all measurements unchanged. Charged channels transform; neutral do not.
- **Fusion mask is a veto.** `0` = forbidden, `1` = allowed (no soft weights).
- **Layer isolation.** No directed edge appears twice in a single DAG layer. Double‑buffering prevents read/write conflict.
- **No implicit normalization.** Never rescale or renormalize counts.

---

## 1. Data model changes
### 1.1 Tensors
- **Counts:** `counts : int32 [E, C, k]`
- **Fusion mask:** `fusion_mask : uint8 [E, C, k]` or sparse (see §2.2).
- **Gauge phases:** `gauge : uint8 [V]` (node‑local reference). Applies only to **charged** channels.
- **Edge phase offsets:** `edge_offset : uint8 [E]` (per directed edge via `edge_ref`).
- **Channel table (metadata):**
  ```yaml
  channels:
    - { name: e_minus, charge: -1, neutral: false }
    - { name: e_plus,  charge: +1, neutral: false }
    - { name: mu_minus,charge: -1, neutral: false }
    - { name: mu_plus, charge: +1, neutral: false }
    - { name: gamma,   charge:  0, neutral: true  }
  ```
  Loader assigns channel indices `0..C-1` in order.

### 1.2 YAML version tag
- `irrepnet_dm: "0.2"`  (loader may lift `"0.1"` → `"0.2"`; see §6).

---

## 2. Scenario file (v0.2 additions)
### 2.1 Channels
```yaml
channels:
  - { name: e_minus, charge: -1, neutral: false }
  - { name: e_plus,  charge: +1, neutral: false }
  - { name: gamma,   charge:  0, neutral: true  }
```

### 2.2 Fusion mask (choose exactly one form)
- **Dense:** `fusion_mask : [E][C][k]` of {0,1}.
- **Sparse:** list of (edge,channel) items enabling phases:
  ```yaml
  fusion_mask_sparse:
    - edge_id: 12
      channel: e_minus        # or channel index
      allow_phases: [0,4,6]
    - edge_id: 7
      channel: gamma
      allow_phases: [0,1,2,3,4,5,6,7]
  ```

### 2.3 Coupling rules (node‑local, post‑propagation)
Each tick and layer, after propagation/masking, **coupling** fires on each node using the multiset of incoming bundles (counts aggregated by `(channel,phase)` from inbound edges selected in the layer).

Minimal rule schema:
```yaml
coupling_rules:
  - name: brems_emit
    scope: { nodes: "any", edges: "scatter_zone" }   # optional subgroup tags
    in:   [{ ch: e_minus, min: 1 }]
    out:  [{ ch: e_minus, add: 1 }, { ch: gamma, add: 1 }]
    phase:
      gamma: "delta"     # emitted gamma phase (see §3.3)
      e_minus: "inherit" # keep incoming phase
```

Optional trigger:
```yaml
    trigger:
      kind: "loop_resonance_drop"
      tag:  "positronium"
```

### 2.4 Counts initialization
```yaml
counts_init:
  - { edge: 0, channel: e_minus, phase: 0, value: 100 }
  - { edge: 5, channel: gamma,   phase: 0, value: 0 }
```

---

## 3. Evolution semantics
Per DAG layer:
1. **Select edges** `I` in this layer.
2. **Propagate counts** (vectorized across channels):
   - For **charged** channel `c`:
     `Δ = (gauge[src] - gauge[dst] + edge_offset[e]) % k` → circular shift.
   - For **neutral** channel (e.g., `gamma`):
     `Δ = edge_offset[e] % k` (no gauge term).
3. **Apply fusion mask** on `[E,C,k]` slice.
4. **Accumulate** to `counts_next` for all outgoing edges of `dst`, per channel.
5. **Node‑local coupling** on nodes touched this layer:
   - Read incoming `(ch,phase)` counts now present in `counts_next`.
   - For each matching rule: check `in` requirements, produce `out`, assign phases (§3.3), `index_add_` onto **outgoing edges** of that node.
6. Swap buffers; proceed to next layer.

### 3.1 Determinism
Counts are integers; rules are deterministic (no RNG).

### 3.2 Charge conservation
Unless a rule is marked `nonconservative: true`, enforce per‑tick conservation with assertion using channel `charge` metadata.

### 3.3 Phase assignment keywords
- `"inherit"`: copy phase of a specified input channel.
- `"sum"`: `(phase_a + phase_b + …) % k`.
- `"delta"`: use local propagation Δ on the emitting edge.
- `"fixed:p"`: constant integer phase `p∈[0,k-1]`.

---

## 4. Measurement
Roots‑of‑unity projection with optional channel filter:
```yaml
measurement:
  representation: "roots_of_unity"
  outputs:
    - { name: "gamma_out_R", readout_edges: [17,18], channels: [gamma] }
    - { name: "lepton_L",   readout_edges: [2,3,4], channels: [e_minus,e_plus] }
```
If `channels` omitted, sum across all channels first.

---

## 5. Example fragments
### 5.1 Channels + masks
```yaml
irrepnet_dm: "0.2"
phase_group: { kind: "Zk", k: 8 }

channels:
  - { name: e_minus, charge: -1, neutral: false }
  - { name: e_plus,  charge: +1, neutral: false }
  - { name: gamma,   charge:  0, neutral: true  }

fusion_mask_sparse:
  - { edge_id: 0, channel: e_minus, allow_phases: [0,4] }
  - { edge_id: 0, channel: e_plus,  allow_phases: [0,4] }
  - { edge_id: 7, channel: gamma,   allow_phases: [0,1,2,3,4,5,6,7] }
```

### 5.2 Bremsstrahlung‑like emission
```yaml
coupling_rules:
  - name: brems_emit
    scope: { edges: "scatter_zone" }
    in:   [{ ch: e_minus, min: 1 }]
    out:  [{ ch: e_minus, add: 1 }, { ch: gamma, add: 1 }]
    phase: { gamma: "delta", e_minus: "inherit" }
```

### 5.3 Positronium‑like loop transition
```yaml
coupling_rules:
  - name: ps_transition_emit
    trigger: { kind: "loop_resonance_drop", tag: "positronium" }
    in:   [{ ch: e_minus, min: 1 }, { ch: e_plus, min: 1 }]
    out:  [{ ch: e_minus, add: 1 }, { ch: e_plus, add: 1 }, { ch: gamma, add: 1 }]
    phase: { gamma: "fixed:4" }      # discrete line (k=8)
```

---

## 6. Migration from v0.1
- Loader accepts `"0.1"` and **lifts** to v0.2 by creating a single implicit neutral channel and expanding shapes: `[E,k] → [E,1,k]`.
- If both explicit `channels` and v0.1 shapes present, raise `E_V10_V20_CONFLICT` to force an explicit choice.

---

## 7. Tests
1. Shape sanity: `[E,C,k]` and masks line up.
2. Gauge invariance for charged channels; neutral ignores gauge.
3. Reproduce v0.1 two‑path interference with a single charged channel.
4. Neutral propagation responds only to `edge_offset`.
5. Bremsstrahlung rule increases `gamma` and conserves charge.
6. Determinism from reset.
7. Mask veto ⇒ zero measurement.
8. Charge conservation assertions pass for conservative rules.

---

## 8. Implementation checklist
- **loader.py**: parse channels, lift v0.1, expand masks (dense/sparse), build channel index map.
- **sim.py**: upgrade buffers to `[E,C,k]`; per‑channel Δ; channel‑wise masking; vectorized accumulation; node‑local coupling engine.
- **measure.py**: support `channels` filter.
- **examples/**: add `cloud_v01.yaml` (beam through loops with `brems_emit`).

---

## 9. Principle
> We evolve **discrete correlation counts** with mod‑k bookkeeping.  
> The only continuous object is the **phasor at readout**.

