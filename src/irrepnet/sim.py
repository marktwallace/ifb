
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Sequence, Tuple

import torch

from .loader import (
    ChannelSpec,
    CountInitEntry,
    CouplingRule,
    DirectedEdge,
    MeasurementReadout,
    PhaseInstruction,
    Scenario,
    load_scenario,
)
from .measure import measure_counts


class IRREPnetSim:
    """
    Integer-only propagation for IRREPnet scenarios.
    Supports multi-channel edges, deterministic coupling, and tag-scoped emissions.
    """

    def __init__(self, scenario_file: str, device: torch.device | None = None):
        self.scenario_path = scenario_file
        self.scenario: Scenario = load_scenario(scenario_file)
        self.device = self._select_device(device)
        self._build()

    def _select_device(self, device: torch.device | None) -> torch.device:
        if device is not None:
            return device
        if torch.backends.mps.is_available():
            return torch.device("mps")
        if torch.cuda.is_available():
            return torch.device("cuda")
        return torch.device("cpu")

    def _build(self) -> None:
        scenario = self.scenario
        self.k = scenario.k
        self.num_channels = len(scenario.channels)
        self.num_edges = len(scenario.directed_edges)
        self.num_nodes = scenario.node_count

        self.gauge = torch.tensor(scenario.node_gauge, dtype=torch.uint8, device=self.device)
        self.node_tags = [set(tags) for tags in scenario.node_tags]

        self.src = torch.tensor([edge.src for edge in scenario.directed_edges], dtype=torch.int64, device=self.device)
        self.dst = torch.tensor([edge.dst for edge in scenario.directed_edges], dtype=torch.int64, device=self.device)
        self.edge_offset = torch.tensor(
            [edge.phase_offset for edge in scenario.directed_edges],
            dtype=torch.uint8,
            device=self.device,
        )
        self.edge_tags = [set(edge.tags) for edge in scenario.directed_edges]

        self.channels: List[ChannelSpec] = list(scenario.channels)
        self.channel_is_neutral = torch.tensor(
            [1 if ch.neutral else 0 for ch in self.channels],
            dtype=torch.bool,
            device=self.device,
        )
        self.channel_charges = torch.tensor(
            [ch.charge for ch in self.channels],
            dtype=torch.int32,
            device=self.device,
        )
        self.any_neutral_channel = bool(self.channel_is_neutral.any().item())

        self.fusion_mask = torch.tensor(scenario.fusion_mask, dtype=torch.uint8, device=self.device)

        self.counts = torch.zeros(
            (self.num_edges, self.num_channels, self.k),
            dtype=torch.int32,
            device=self.device,
        )
        self.counts_next = torch.zeros_like(self.counts)

        self._init_counts(scenario.counts_init)

        self.layers = [list(layer) for layer in scenario.layers]
        self.repeat = scenario.repeat
        self.readouts = list(scenario.measurement)
        self.coupling_rules = list(scenario.coupling_rules)

        self.phase_range = torch.arange(self.k, dtype=torch.int64, device=self.device)

        self.out_index: List[List[int]] = [[] for _ in range(self.num_nodes)]
        for edge_idx, edge in enumerate(scenario.directed_edges):
            self.out_index[edge.src].append(edge_idx)

    def _init_counts(self, counts_init: Sequence[CountInitEntry]) -> None:
        for entry in counts_init:
            self.counts[entry.edge, entry.channel, entry.phase] += int(entry.value)

    def reset(self) -> None:
        self.scenario = load_scenario(self.scenario_path)
        self._build()

    def step(self) -> None:
        for _ in range(self.repeat):
            for edge_indices in self.layers:
                if not edge_indices:
                    continue
                self._apply_layer(edge_indices)
                self.counts, self.counts_next = self.counts_next, self.counts
                self.counts_next.zero_()

    @torch.no_grad()
    def _apply_layer(self, edges: Sequence[int]) -> None:
        device = self.device
        edge_idx = torch.tensor(edges, dtype=torch.int64, device=device)
        src = self.src.index_select(0, edge_idx)
        dst = self.dst.index_select(0, edge_idx)
        offsets = self.edge_offset.index_select(0, edge_idx).to(torch.int16)

        gauge_src = self.gauge.index_select(0, src).to(torch.int16)
        gauge_dst = self.gauge.index_select(0, dst).to(torch.int16)

        delta_base = (gauge_src - gauge_dst + offsets) % self.k  # [E_sel]
        delta_neutral = (offsets % self.k).to(torch.int64)

        delta = delta_base.unsqueeze(1).repeat(1, self.num_channels).to(torch.int64)
        if self.any_neutral_channel:
            neutral_mask = self.channel_is_neutral
            delta[:, neutral_mask] = delta_neutral.unsqueeze(1)

        shift = (self.phase_range.view(1, 1, -1) - delta.unsqueeze(-1)) % self.k  # [E_sel, C, k]

        src_counts = self.counts.index_select(0, edge_idx)  # [E_sel, C, k]
        shifted = src_counts.gather(2, shift)  # [E_sel, C, k]

        mask = self.fusion_mask.index_select(0, edge_idx).to(torch.int32)
        allowed = shifted.to(torch.int32) * mask  # [E_sel, C, k]

        node_incoming: Dict[int, torch.Tensor] = {}
        nodes_touched: List[int] = []
        for row, node in enumerate(dst.tolist()):
            allowed_slice = allowed[row]
            if node not in node_incoming:
                node_incoming[node] = torch.zeros(
                    (self.num_channels, self.k),
                    dtype=torch.int32,
                    device=device,
                )
                nodes_touched.append(node)
            node_incoming[node].add_(allowed_slice)

            for target_edge in self.out_index[node]:
                self.counts_next[target_edge] += allowed_slice

        if not self.coupling_rules:
            return

        for node in nodes_touched:
            incoming = node_incoming[node]
            if incoming.sum().item() == 0:
                continue
            self._apply_coupling(node, incoming)

    def _apply_coupling(self, node_idx: int, incoming: torch.Tensor) -> None:
        node_tags = self.node_tags[node_idx]
        if not self.coupling_rules or not self.out_index[node_idx]:
            return

        working = incoming.clone()
        staged_outputs: List[Tuple[CouplingRule, List[int], List[Tuple[int, torch.Tensor, PhaseInstruction]]]] = []

        for rule in self.coupling_rules:
            if rule.node_tags_any:
                scope = set(rule.node_tags_any)
                if node_tags.isdisjoint(scope):
                    continue

            target_edges = self._select_target_edges(node_idx, rule)
            if not target_edges:
                continue

            multiplicity = self._rule_multiplicity(working, rule)
            if multiplicity <= 0:
                continue

            consumed = self._consume_inputs(working, rule, multiplicity)
            emissions = self._build_rule_emissions(rule, consumed, multiplicity)
            if not emissions:
                continue

            staged_outputs.append((rule, target_edges, emissions))

        for rule, target_edges, emissions in staged_outputs:
            for channel_idx, hist, instr in emissions:
                if hist.sum().item() == 0:
                    continue
                for edge_idx in target_edges:
                    applied = self._apply_phase_instruction(channel_idx, hist, instr, edge_idx)
                    self.counts_next[edge_idx, channel_idx, :] += applied

    def _select_target_edges(self, node_idx: int, rule: CouplingRule) -> List[int]:
        edges = self.out_index[node_idx]
        if not edges:
            return []
        if not rule.out_edge_tags_any:
            return edges
        scope = set(rule.out_edge_tags_any)
        return [edge for edge in edges if not self.edge_tags[edge].isdisjoint(scope)]

    def _rule_multiplicity(self, inventory: torch.Tensor, rule: CouplingRule) -> int:
        if not rule.inputs:
            return 0
        counts = []
        for inp in rule.inputs:
            total = int(inventory[inp.channel].sum().item())
            counts.append(total // inp.minimum if inp.minimum > 0 else 0)
        return min(counts) if counts else 0

    def _consume_inputs(
        self,
        inventory: torch.Tensor,
        rule: CouplingRule,
        multiplicity: int,
    ) -> Dict[int, torch.Tensor]:
        consumed: Dict[int, torch.Tensor] = {}
        for inp in rule.inputs:
            needed = multiplicity * inp.minimum
            channel_counts = inventory[inp.channel]
            consumed_hist = torch.zeros(self.k, dtype=torch.int32, device=self.device)
            if needed == 0:
                consumed[inp.channel] = consumed_hist
                continue
            for phase_index in range(self.k):
                if needed <= 0:
                    break
                available = int(channel_counts[phase_index].item())
                if available == 0:
                    continue
                take = min(available, needed)
                channel_counts[phase_index] -= take
                consumed_hist[phase_index] += take
                needed -= take
            if needed != 0:
                raise RuntimeError(f"E_RULE_CONSUME_DEFICIT: {rule.name}")
            consumed[inp.channel] = consumed_hist
        return consumed

    def _build_rule_emissions(
        self,
        rule: CouplingRule,
        consumed: Dict[int, torch.Tensor],
        multiplicity: int,
    ) -> List[Tuple[int, torch.Tensor, PhaseInstruction]]:
        emissions: List[Tuple[int, torch.Tensor, PhaseInstruction]] = []
        for output in rule.outputs:
            total = multiplicity * output.add
            if total <= 0:
                continue
            instr = rule.phase.get(output.channel)
            if instr is None:
                continue
            histogram = self._materialize_histogram(instr, output.channel, total, consumed, rule)
            emissions.append((output.channel, histogram, instr))
        return emissions

    def _materialize_histogram(
        self,
        instr: PhaseInstruction,
        channel: int,
        total: int,
        consumed: Dict[int, torch.Tensor],
        rule: CouplingRule,
    ) -> torch.Tensor:
        hist = torch.zeros(self.k, dtype=torch.int32, device=self.device)
        if total == 0:
            return hist

        if instr.kind == "inherit":
            if not instr.sources:
                raise ValueError(f"E_PHASE_INHERIT_SOURCE_MISSING: {rule.name}")
            source = instr.sources[0]
            source_hist = consumed.get(source)
            if source_hist is None:
                return hist
            source_total = int(source_hist.sum().item())
            if source_total == 0:
                return hist
            factor = total // source_total
            if factor * source_total != total:
                raise ValueError(f"E_PHASE_INHERIT_SCALE: {rule.name}")
            hist = source_hist.clone() * factor
            return hist

        if instr.kind == "fixed":
            if instr.value is None:
                raise ValueError(f"E_PHASE_FIXED_VALUE_MISSING: {rule.name}")
            phase_index = instr.value % self.k
            hist[phase_index] = total
            return hist

        if instr.kind == "delta":
            hist[0] = total
            return hist

        if instr.kind == "sum":
            raise NotImplementedError("Phase keyword 'sum' is not yet implemented")

        raise ValueError(f"E_PHASE_KIND_UNKNOWN: {instr.kind}")

    def _apply_phase_instruction(
        self,
        channel: int,
        histogram: torch.Tensor,
        instr: PhaseInstruction,
        edge_idx: int,
    ) -> torch.Tensor:
        if instr.kind == "delta":
            delta = self._edge_channel_delta(channel, edge_idx)
            return torch.roll(histogram, shifts=int(delta), dims=0)
        return histogram

    def _edge_channel_delta(self, channel: int, edge_idx: int) -> int:
        base = int(self.edge_offset[edge_idx].item()) % self.k
        if self.channel_is_neutral[channel]:
            return base
        src = int(self.src[edge_idx].item())
        dst = int(self.dst[edge_idx].item())
        gauge_src = int(self.gauge[src].item())
        gauge_dst = int(self.gauge[dst].item())
        return (gauge_src - gauge_dst + base) % self.k

    def measure(self) -> Dict[str, float]:
        results: Dict[str, float] = {}
        for readout in self.readouts:
            results[readout.name] = measure_counts(
                self.counts,
                list(readout.edges),
                self.k,
                channels=list(readout.channels) if readout.channels is not None else None,
            )
        return results

    def export_state(self) -> Dict[str, Any]:
        return {
            "k": self.k,
            "counts_shape": list(self.counts.shape),
            "counts_checksum": int(self.counts.sum().item() % 2_147_483_647),
            "device": str(self.device),
        }
