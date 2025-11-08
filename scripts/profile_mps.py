#!/usr/bin/env python3
from __future__ import annotations
import argparse
import time
import torch
from irrepnet import IRREPnetSim

def main():
    p = argparse.ArgumentParser(description="Profile step() throughput and report device.")
    p.add_argument("scenario", type=str, help="Path to scenario YAML")
    p.add_argument("--warmup", type=int, default=5, help="Warmup steps not timed")
    p.add_argument("--steps", type=int, default=100, help="Timed steps")
    p.add_argument("--device", type=str, default=None, choices=[None, "cpu", "cuda", "mps"],
                   help="Force device (default: auto-detect)")
    args = p.parse_args()

    # device select
    device = None
    if args.device == "cpu":
        device = torch.device("cpu")
    elif args.device == "cuda":
        assert torch.cuda.is_available(), "CUDA not available"
        device = torch.device("cuda")
    elif args.device == "mps":
        assert torch.backends.mps.is_available(), "MPS not available"
        device = torch.device("mps")

    sim = IRREPnetSim(args.scenario, device=device)
    print(f"device = {sim.device}")

    # warmup
    t0 = time.perf_counter()
    for _ in range(args.warmup):
        sim.step()
    torch.mps.synchronize() if str(sim.device) == "mps" else None
    torch.cuda.synchronize() if str(sim.device) == "cuda" else None
    t1 = time.perf_counter()

    # timed
    t2 = time.perf_counter()
    for _ in range(args.steps):
        sim.step()
    torch.mps.synchronize() if str(sim.device) == "mps" else None
    torch.cuda.synchronize() if str(sim.device) == "cuda" else None
    t3 = time.perf_counter()

    warmup_s = t1 - t0
    total_s  = t3 - t2
    per_step = total_s / max(1, args.steps)

    print(f"warmup: {args.warmup} steps in {warmup_s:.4f}s")
    print(f"timed : {args.steps} steps in {total_s:.4f}s  → {per_step*1000:.3f} ms/step")

if __name__ == "__main__":
    main()
