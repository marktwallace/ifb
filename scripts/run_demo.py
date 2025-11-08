# scripts/run_demo.py
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def _ensure_src_on_path() -> None:
    """Allow running the script from a checkout without `pip install -e .`."""
    try:
        root = Path(__file__).resolve().parents[1]
    except (NameError, RuntimeError):
        return

    src = root / "src"
    if src.exists():
        src_str = str(src)
        if src_str not in sys.path:
            sys.path.insert(0, src_str)


_ensure_src_on_path()

from irrepnet import IRREPnetSim

def main():
    parser = argparse.ArgumentParser(description="Run an IRREPnet scenario and print measurement results.")
    parser.add_argument(
        "scenario",
        type=str,
        help="Path to a scenario YAML file, e.g. examples/two_path_v01.yaml"
    )
    parser.add_argument(
        "--steps",
        type=int,
        default=1,
        help="Number of full DAG step cycles to apply before measuring (default: 1).",
    )
    args = parser.parse_args()

    sim = IRREPnetSim(args.scenario)
    for _ in range(args.steps):
        sim.step()

    results = sim.measure()
    print("\n=== Measurement Results ===")
    for name, val in results.items():
        print(f"{name:20s}  {val:.6f}")

    print("\n=== State Export Check ===")
    print(sim.export_state())

if __name__ == "__main__":
    main()
