# cloud_v01 debug patch (v0.2)

## 1) Replace DAG section with pipeline

```yaml
dag:
  layers:
    - { edges: [0] }     # 0 -> 1
    - { edges: [2] }     # 1 -> 2 (arrives at scatter node)
    # coupling fires here at node 2
    - { edges: [8] }     # 2 -> 6 (gamma to detector)
    - { edges: [4] }     # 2 -> 4 (corridor continues right, optional)
    - { edges: [6] }     # 4 -> 5 (electron to R detector, optional)
  repeat: 8
```

## 2) Modify `brems_emit` to target gamma_line edges only

```yaml
coupling_rules:
  - name: brems_emit
    scope: { nodes_any: ["scatter_zone"], out_edges_any: ["gamma_line"] }
    in:   [{ ch: e_minus, min: 1 }]
    out:  [{ ch: e_minus, add: 1 }, { ch: gamma, add: 1 }]
    phase: { gamma: "delta", e_minus: "inherit" }
```

## 3) Optional debug rule (use if gamma still zero)

```yaml
  - name: brems_emit_debug
    scope: { nodes_any: ["scatter_zone"], out_edges_any: ["gamma_line"] }
    in:   [{ ch: e_minus, min: 1 }]
    out:  [{ ch: e_minus, add: 1 }, { ch: gamma, add: 1 }]
    phase: { gamma: "fixed:0", e_minus: "inherit" }
```

## 4) Expected behavior after patch

- Electron pulse reaches node 2 in layer 2.
- `brems_emit` fires, producing gamma on edge 8.
- `gamma_out_R` measurement becomes nonzero.
- `counts_checksum` > 200 indicates rule activity.

## 5) Quick test sequence

```
make cloud
# or, if using run_demo directly:
python scripts/run_demo.py examples/cloud_v01.yaml
```
