#!/usr/bin/env python3
from __future__ import annotations
import argparse
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
from irrepnet import IRREPnetSim

def main():
    p = argparse.ArgumentParser(description="Animate counts over (edge, phase) during evolution.")
    p.add_argument("scenario", type=str, help="Path to scenario YAML")
    p.add_argument("--frames", type=int, default=30, help="Number of frames (step() calls) to animate")
    p.add_argument("--interval", type=int, default=200, help="Milliseconds between frames")
    p.add_argument("--show", action="store_true", help="Show animation window")
    p.add_argument("--save", type=str, default=None, help="Save animation to file (e.g., out/anim.gif or out/anim.mp4)")
    p.add_argument(
        "--channels",
        nargs="*",
        default=None,
        help="Channel names to include (default: all channels).",
    )
    p.add_argument(
        "--split-channels",
        action="store_true",
        help="Animate each selected channel in its own panel instead of summing them.",
    )
    p.add_argument(
        "--dump",
        type=str,
        default=None,
        help="Optional path to write per-frame per-channel edge sums as JSON.",
    )
    args = p.parse_args()

    sim = IRREPnetSim(args.scenario)

    # capture initial state
    snapshots = []
    snapshots.append(sim.counts.detach().to("cpu").numpy())

    for _ in range(args.frames):
        sim.step()
        snapshots.append(sim.counts.detach().to("cpu").numpy())

    raw = np.stack(snapshots, axis=0)  # [T+1, E, C, K]

    channel_names = [ch.name for ch in sim.scenario.channels]
    if args.channels:
        selected_indices = []
        for name in args.channels:
            if name not in channel_names:
                raise SystemExit(f"Unknown channel '{name}'. Available: {channel_names}")
            selected_indices.append(channel_names.index(name))
    else:
        selected_indices = list(range(len(channel_names)))
    if not selected_indices:
        raise SystemExit("No channels selected for animation.")
    selected_names = [channel_names[i] for i in selected_indices]

    data = raw[:, :, selected_indices, :]  # [T+1, E, C_sel, K]
    T = data.shape[0]

    aggregated_for_dump = data.sum(axis=3)  # [T+1, E, C_sel]

    if args.dump:
        dump_payload = []
        for frame_idx in range(T):
            frame_entry = {"frame": frame_idx, "channels": {}}
            for ci, name in enumerate(selected_names):
                edge_values = aggregated_for_dump[frame_idx, :, ci]
                nonzero = {int(edge_idx): int(val) for edge_idx, val in enumerate(edge_values) if val != 0}
                if nonzero:
                    frame_entry["channels"][name] = nonzero
            dump_payload.append(frame_entry)
        with open(args.dump, "w", encoding="utf-8") as fh:
            json.dump(dump_payload, fh, indent=2)

    if args.split_channels and len(selected_indices) > 1:
        E, K = data.shape[1], data.shape[3]
        fig, axes = plt.subplots(len(selected_indices), 1, sharex=True, figsize=(8, 3 * len(selected_indices)))
        if len(selected_indices) == 1:
            axes = [axes]
        ims = []
        for idx, ax in enumerate(axes):
            im = ax.imshow(data[0, :, idx, :], aspect="auto", origin="lower")
            ax.set_ylabel("directed edge index")
            ax.set_title(f"Channel: {selected_names[idx]} — frame 0/{T-1}")
            ims.append(im)
        axes[-1].set_xlabel("phase (0..k-1)")
        fig.colorbar(ims[0], ax=axes, label="count")

        def update(frame):
            for idx, im in enumerate(ims):
                im.set_data(data[frame, :, idx, :])
                axes[idx].set_title(f"Channel: {selected_names[idx]} — frame {frame}/{T-1}")
            return tuple(ims)

        anim = FuncAnimation(fig, update, frames=T, interval=args.interval, blit=False)
    else:
        summed = data.sum(axis=2)  # [T+1, E, K]
        T, E, K = summed.shape
        fig, ax = plt.subplots()
        im = ax.imshow(summed[0], aspect="auto", origin="lower")
        ax.set_xlabel("phase (0..k-1)")
        ax.set_ylabel("directed edge index")
        label = ", ".join(selected_names) if selected_names else "all channels"
        ax.set_title(f"Counts over (edge, phase) — {label} — frame 0/{T-1}")

        cbar = fig.colorbar(im, ax=ax)
        cbar.set_label("count")

        def update(frame):
            im.set_data(summed[frame])
            ax.set_title(f"Counts over (edge, phase) — {label} — frame {frame}/{T-1}")
            return (im,)

        anim = FuncAnimation(fig, update, frames=T, interval=args.interval, blit=False)

    if args.save:
        os.makedirs(os.path.dirname(args.save), exist_ok=True)
        if args.save.lower().endswith(".gif"):
            anim.save(args.save, writer=PillowWriter(fps=max(1, int(1000/args.interval))))
        else:
            # mp4 requires ffmpeg; fallback to gif if not available
            try:
                anim.save(args.save, writer="ffmpeg", fps=max(1, int(1000/args.interval)))
            except Exception:
                alt = os.path.splitext(args.save)[0] + ".gif"
                anim.save(alt, writer=PillowWriter(fps=max(1, int(1000/args.interval))))
                print(f"[warn] ffmpeg not available; wrote {alt} instead")
    if args.show or not args.save:
        plt.show()

if __name__ == "__main__":
    main()
