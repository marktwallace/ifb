#!/usr/bin/env python3
from __future__ import annotations
import argparse
import os
import matplotlib.pyplot as plt
from irrepnet import IRREPnetSim

def main():
    p = argparse.ArgumentParser(description="Sweep one node's gauge phase and plot measurement vs phase.")
    p.add_argument("scenario", type=str, help="Path to scenario YAML (e.g., examples/two_path_v01.yaml)")
    p.add_argument("--node", type=int, default=2, help="Node id to sweep (default: 2)")
    p.add_argument("--output", type=str, default="det_A", help="Measurement output name (default: det_A)")
    p.add_argument("--steps", type=int, default=1, help="Steps per phase setting (default: 1)")
    p.add_argument("--show", action="store_true", help="Show interactive plot window")
    p.add_argument("--save", type=str, default=None, help="Save plot to this path (e.g., out/scan.png)")
    args = p.parse_args()

    sim = IRREPnetSim(args.scenario)
    k = sim.k

    phases = list(range(k))
    vals = []
    for g in phases:
        sim.reset()
        # override just this node’s gauge for the run
        sim.gauge[args.node] = g
        for _ in range(args.steps):
            sim.step()
        m = sim.measure()
        vals.append(float(m.get(args.output, 0.0)))

    # plotting
    fig, ax = plt.subplots()
    ax.plot(phases, vals, marker="o")
    ax.set_xlabel("Gauge phase (mod k)")
    ax.set_ylabel(f"Measurement: {args.output}")
    ax.set_title(f"Sweep node={args.node} over Z_{k}")

    if args.save:
        os.makedirs(os.path.dirname(args.save), exist_ok=True)
        fig.savefig(args.save, bbox_inches="tight", dpi=150)
    if args.show or not args.save:
        plt.show()

if __name__ == "__main__":
    main()
