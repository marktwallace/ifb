# IFB — It From Bit Simulator (IRREPnet v0.2)

A discrete, finite-state simulation framework for propagating **phase-labeled integer history counts** across a directed graph, with **local update rules** and **emergent interference**.  
Built intentionally **without** wavefunctions, continuous fields, differentiable manifolds, or Hilbert spaces.

This repo implements **IRREPnet v0.2** — the *multi-channel* model:
- Phase group = **Zₖ** (k finite, typically 8–64)
- All state evolution is **integer-only**
- Channels propagate on directed edges with **per-channel fusion masks**
- Deterministic, tag-scoped **coupling rules** fire after each layer
- Time = **ordered update schedule over directed edges**
- Geometry is **not stored**; correlation structure is primary
- Measurement = **phasor sum over phase bins** at readout only

The model is **computational**, not symbolic or interpretive.

---

## ⚡ Motivation (Concise)

The goal is to explore:
- Interference
- Entanglement structure
- Gauge-like phase redundancy
- Emergent momentum / wave dispersion

…in a framework where:
- No continuum is assumed
- No amplitudes are fundamental
- No “hidden geometry” is presupposed

This is a **testbed** for reasoning about **finite, discrete physical models**.

Not a replacement for QFT; rather a platform to study **information-first dynamics**.

So *why* am I doing this? Here is the [long version](WHY.md).

---

## 🧱 Core Model Summary (IRREPnet v0.2)

| Concept | Representation |
|---|---|
| Phase | u8 mod k (`Z_k`) |
| State | `counts[e, c, g]` = integer microhistory counts on directed edges |
| Dynamics | integer-only propagation with per-channel circular phase shift + mask |
| Coupling | deterministic, tag-scoped rules (consume `W`, emit `Q`) |
| Interference | occurs only at measurement stage via phasor sum |
| Time | execution order of DAG layers (no continuous t) |
| Geometry | emergent from stable entanglement adjacency (not stored) |

Full spec: `docs/irrepnet_v0.2_spec_unified.md`

---

## 🧩 Repository Structure

```
ifb/
  docs/
    irrepnet_v0.2_spec_unified.md
    spec_v0.1_compact.md
  src/
    irrepnet/
      __init__.py
      sim.py
      loader.py
      measure.py
  tests/
    test_two_path.py
    test_triangle_loop.py
    test_chain_momentum.py
  examples/
    two_path_v01.yaml
    triangle_loop_v01.yaml
    chain_momentum_v01.yaml
    cloud_v01.yaml
  README.md
  pyproject.toml
  requirements.txt
```

---

## 🛠️ Environment Setup (Python 3.12 + PyTorch + MPS)

With mamba:

```bash
mamba env create -f environment.yml
mamba activate ifb
mamba run -n ifb python -m ipykernel install --user --name ifb --display-name "Python (ifb)"
cd ifb
# test
python scripts/run_demo.py examples/two_path_v01.yaml
```

To get the notebook working:

```bash
mamba activate ifb
mamba run -n ifb python -m ipykernel install --user --name ifb --display-name "Python (ifb)"
pip install -e .
python -c "import irrepnet, inspect; print(irrepnet.__file__)"
```


Or do this if no mamba:

```bash
brew install python@3.12
python3.12 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install torch --index-url https://download.pytorch.org/whl/cpu
```




Verify MPS:
```python
import torch
torch.backends.mps.is_available()
```

## Demos & Tools

Install plotting deps:

```bash
mamba install matplotlib  # or: pip install matplotlib
```

1) Gauge phase sweep (interference curve)

Sweeps one node’s gauge phase over Z_k and plots a measurement.

```bash
python scripts/scan_gauge_phase.py examples/two_path_v01.yaml \
  --node 2 \
  --output det_A \
  --steps 1 \
  --save out/scan_two_path.png   # or --show
```

2) Animate counts over (edge, phase)

Shows a heatmap animation of counts across directed edges and phase bins.
```bash
python scripts/animate_counts.py examples/triangle_loop_v01.yaml \
  --frames 40 \
  --interval 150 \
  --save out/triangle_anim.gif   # or --show
```

Notes:

If ffmpeg is installed, you can save .mp4 (e.g., --save out/anim.mp4).

Without ffmpeg, the script will fall back to .gif.

3) Profile performance

Times step() on your current device (CPU, CUDA, or Apple MPS).
```bash
python scripts/profile_mps.py examples/chain_momentum_v01.yaml \
  --warmup 5 \
  --steps 200
```

---

## ▶️ Development Workflow

1. Implement loader (`loader.py`) with v0.2 schema + migration
2. Implement multi-channel propagation & coupling engine (`sim.py`)
3. Validate using example scenarios (`examples/`)
4. Run operator checklist & profiling scripts
5. Iterate on performance/visualization

Use CPU first, then:
```python
device = torch.device("mps")
```

---

## ✅ Milestones

| Stage | Goal |
|---|---|
| v0.1 | Single-channel IRREPnet w/ measurement |
| v0.2 | Multi-channel propagation + deterministic coupling |
| v0.3 | Benchmarking + visualization |
| v0.4 | Geometry diagnostics |

---

## 🧭 Philosophy

- Finite first.
- No configuration space.
- Complexity must be earned.
- Interpretation is downstream.

---

## License

MIT
