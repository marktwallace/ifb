
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import yaml


@dataclass(frozen=True)
class PhaseInstruction:
    kind: str
    sources: Tuple[int, ...] = ()
    value: Optional[int] = None


@dataclass(frozen=True)
class RuleInput:
    channel: int
    minimum: int
    sum_over_phases: bool


@dataclass(frozen=True)
class RuleOutput:
    channel: int
    add: int


@dataclass(frozen=True)
class CouplingRule:
    name: str
    inputs: Tuple[RuleInput, ...]
    outputs: Tuple[RuleOutput, ...]
    phase: Dict[int, PhaseInstruction]
    node_tags_any: Optional[Tuple[str, ...]]
    out_edge_tags_any: Optional[Tuple[str, ...]]
    nonconservative: bool
    charge_balance: int


@dataclass(frozen=True)
class ChannelSpec:
    name: str
    charge: int
    neutral: bool


@dataclass(frozen=True)
class DirectedEdge:
    id: int
    src: int
    dst: int
    edge_ref: int
    phase_offset: int
    tags: Tuple[str, ...]


@dataclass(frozen=True)
class CountInitEntry:
    edge: int
    channel: int
    phase: int
    value: int


@dataclass(frozen=True)
class MeasurementReadout:
    name: str
    edges: Tuple[int, ...]
    channels: Optional[Tuple[int, ...]]


@dataclass
class Scenario:
    version: str
    k: int
    node_count: int
    node_gauge: List[int]
    node_tags: List[Tuple[str, ...]]
    directed_edges: List[DirectedEdge]
    edge_index_by_id: Dict[int, int]
    fusion_mask: List[List[List[int]]]
    channels: List[ChannelSpec]
    channel_index: Dict[str, int]
    counts_init: List[CountInitEntry]
    layers: List[List[int]]
    repeat: int
    measurement: List[MeasurementReadout]
    coupling_rules: List[CouplingRule]


def load_scenario(path: str) -> Scenario:
    with open(path, "r", encoding="utf-8") as handle:
        raw: Dict[str, Any] = yaml.safe_load(handle)

    version = str(raw.get("irrepnet_dm", ""))
    if version != "0.2":
        raise ValueError("E_VERSION_MISMATCH: irrepnet_dm must be '0.2'")

    return _parse_v02(raw)


# --------------------------------------------------------------------------- #
# Parsing helpers


def _parse_v02(raw: Dict[str, Any]) -> Scenario:
    phase_group = raw.get("phase_group", {})
    if phase_group.get("kind") != "Zk":
        raise ValueError("E_PHASE_KIND: phase_group.kind must be 'Zk'")
    k = int(phase_group.get("k", 0))
    if not (2 <= k <= 256):
        raise ValueError("E_PHASE_K_INVALID: k must be in [2..256]")

    nodes = raw.get("nodes") or []
    if not nodes:
        raise ValueError("E_NODES_EMPTY")
    node_index: Dict[int, Dict[str, Any]] = {}
    for entry in nodes:
        nid = int(entry["id"])
        if nid in node_index:
            raise ValueError("E_DUP_NODE_ID")
        node_index[nid] = entry

    node_ids = sorted(node_index.keys())
    if node_ids != list(range(len(node_ids))):
        raise ValueError("E_NODE_ID_GAP: node IDs must be contiguous starting at 0")

    node_gauge: List[int] = []
    node_tags: List[Tuple[str, ...]] = []
    for nid in node_ids:
        entry = node_index[nid]
        gauge = int(entry.get("gauge_phase", 0))
        if not (0 <= gauge < k):
            raise ValueError("E_GAUGE_PHASE_RANGE")
        node_gauge.append(gauge)
        node_tags.append(_normalize_tags(entry.get("tags") or entry.get("tag")))

    edges = raw.get("edges") or []
    if not edges:
        raise ValueError("E_EDGES_EMPTY")
    undirected_by_id: Dict[int, Dict[str, Any]] = {}
    for entry in edges:
        eid = int(entry["id"])
        if eid in undirected_by_id:
            raise ValueError("E_DUP_EDGE_ID")
        undirected_by_id[eid] = entry

    directed_edges_raw = raw.get("directed_edges") or []
    if not directed_edges_raw:
        raise ValueError("E_DIRECTED_EDGES_EMPTY")

    directed_edges: List[DirectedEdge] = []
    edge_index_by_id: Dict[int, int] = {}
    for entry in directed_edges_raw:
        if not entry.get("enabled", True):
            continue
        edge_id = int(entry["id"])
        if edge_id in edge_index_by_id:
            raise ValueError("E_DUP_DIRECTED_EDGE_ID")
        src = int(entry["src"])
        dst = int(entry["dst"])
        if src >= len(node_gauge) or dst >= len(node_gauge):
            raise ValueError("E_DIRECTED_EDGE_NODE_RANGE")
        edge_ref = int(entry["edge_ref"])
        if edge_ref not in undirected_by_id:
            raise ValueError(f"E_DIRECTED_EDGE_REF_INVALID: {edge_ref}")
        base = int(undirected_by_id[edge_ref].get("phase_offset", 0))
        phase_offset = int(entry.get("phase_offset", base)) % k

        tags = _normalize_tags(entry.get("tags"))
        inherited = _normalize_tags(
            undirected_by_id[edge_ref].get("tags") or undirected_by_id[edge_ref].get("tag")
        )
        combined = tuple(sorted(set(tags) | set(inherited)))

        edge_index_by_id[edge_id] = len(directed_edges)
        directed_edges.append(
            DirectedEdge(
                id=edge_id,
                src=src,
                dst=dst,
                edge_ref=edge_ref,
                phase_offset=phase_offset,
                tags=combined,
            )
        )

    if not directed_edges:
        raise ValueError("E_DIRECTED_EDGES_DISABLED")

    channels_raw = raw.get("channels") or []
    if not channels_raw:
        raise ValueError("E_CHANNELS_EMPTY")
    channels: List[ChannelSpec] = []
    channel_index: Dict[str, int] = {}
    for entry in channels_raw:
        name = str(entry["name"])
        if name in channel_index:
            raise ValueError(f"E_DUP_CHANNEL_NAME: {name}")
        charge = int(entry.get("charge", 0))
        neutral = bool(entry.get("neutral", False))
        channel_index[name] = len(channels)
        channels.append(ChannelSpec(name=name, charge=charge, neutral=neutral))

    fusion_mask = _build_fusion_mask(raw, directed_edges, channels, channel_index, k)
    counts_init = _parse_counts_init(raw.get("counts_init"), edge_index_by_id, channel_index, k)
    layers, repeat = _parse_dag(raw.get("dag"), edge_index_by_id)
    measurement = _parse_measurement(raw.get("measurement"), edge_index_by_id, channel_index)
    coupling_rules = _parse_coupling_rules(
        raw.get("coupling_rules"),
        channel_index,
        channels,
        k,
    )

    return Scenario(
        version="0.2",
        k=k,
        node_count=len(node_gauge),
        node_gauge=node_gauge,
        node_tags=node_tags,
        directed_edges=directed_edges,
        edge_index_by_id=edge_index_by_id,
        fusion_mask=fusion_mask,
        channels=channels,
        channel_index=channel_index,
        counts_init=counts_init,
        layers=layers,
        repeat=repeat,
        measurement=measurement,
        coupling_rules=coupling_rules,
    )


def _build_fusion_mask(
    raw: Dict[str, Any],
    directed_edges: Sequence[DirectedEdge],
    channels: Sequence[ChannelSpec],
    channel_index: Dict[str, int],
    k: int,
) -> List[List[List[int]]]:
    dense = raw.get("fusion_mask")
    sparse = raw.get("fusion_mask_sparse")
    if (dense is None) == (sparse is None):
        raise ValueError("E_FUSION_MASK_MISSING: provide exactly one of fusion_mask or fusion_mask_sparse")

    edge_count = len(directed_edges)
    channel_count = len(channels)
    mask = [[[0 for _ in range(k)] for _ in range(channel_count)] for _ in range(edge_count)]

    if dense is not None:
        if len(dense) != edge_count:
            raise ValueError("E_FUSION_MASK_SHAPE")
        for e_idx, per_edge in enumerate(dense):
            if len(per_edge) != channel_count:
                raise ValueError("E_FUSION_MASK_CHANNEL")
            for c_idx, phases in enumerate(per_edge):
                if len(phases) != k:
                    raise ValueError("E_FUSION_MASK_PHASE")
                mask[e_idx][c_idx] = [int(_validate_mask_value(val)) for val in phases]
        return mask

    # sparse
    for entry in sparse:
        e_id = int(entry["edge_id"])
        try:
            e_idx = _resolve_edge_index(e_id, directed_edges)
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError(f"E_FUSION_MASK_EDGE_UNKNOWN: {e_id}") from exc
        channel_raw = entry["channel"]
        c_idx = _resolve_channel_index(channel_raw, channel_index)
        phases = entry.get("allow_phases")
        if not isinstance(phases, Iterable):
            raise ValueError("E_FUSION_MASK_PHASES_INVALID")
        for phase in phases:
            p = int(phase)
            if not (0 <= p < k):
                raise ValueError("E_FUSION_MASK_PHASE_RANGE")
            mask[e_idx][c_idx][p] = 1
    return mask


def _parse_counts_init(
    counts_init: Optional[Sequence[Dict[str, Any]]],
    edge_index_by_id: Dict[int, int],
    channel_index: Dict[str, int],
    k: int,
) -> List[CountInitEntry]:
    if not counts_init:
        return []
    result: List[CountInitEntry] = []
    for entry in counts_init:
        edge_id = int(entry["edge"])
        if edge_id not in edge_index_by_id:
            raise ValueError(f"E_COUNTS_INIT_EDGE_UNKNOWN: {edge_id}")
        channel_raw = entry.get("channel")
        if channel_raw is None:
            raise ValueError("E_COUNTS_INIT_CHANNEL_REQUIRED")
        channel = _resolve_channel_index(channel_raw, channel_index)
        phase = int(entry.get("phase", 0)) % k
        value = int(entry.get("value", 0))
        if value < 0:
            raise ValueError("E_COUNTS_INIT_NEGATIVE_VALUE")
        result.append(
            CountInitEntry(edge=edge_index_by_id[edge_id], channel=channel, phase=phase, value=value)
        )
    return result


def _parse_dag(
    dag: Optional[Dict[str, Any]],
    edge_index_by_id: Dict[int, int],
) -> Tuple[List[List[int]], int]:
    if dag is None:
        raise ValueError("E_DAG_MISSING")
    layers_raw = dag.get("layers")
    if not isinstance(layers_raw, list) or not layers_raw:
        raise ValueError("E_DAG_LAYERS_EMPTY")
    layers: List[List[int]] = []
    for li, layer in enumerate(layers_raw):
        edges_raw = layer.get("edges")
        if not isinstance(edges_raw, list) or not edges_raw:
            raise ValueError(f"E_DAG_LAYER_EMPTY: index {li}")
        seen: set[int] = set()
        converted: List[int] = []
        for edge_id in edges_raw:
            e_id = int(edge_id)
            if e_id not in edge_index_by_id:
                raise ValueError(f"E_DAG_EDGE_UNKNOWN: {e_id}")
            idx = edge_index_by_id[e_id]
            if idx in seen:
                raise ValueError(f"E_DAG_LAYER_CONFLICT: edge {e_id} duplicated in layer {li}")
            seen.add(idx)
            converted.append(idx)
        layers.append(converted)
    repeat = int(dag.get("repeat", 1))
    if repeat < 1:
        raise ValueError("E_DAG_REPEAT_RANGE")
    return layers, repeat


def _parse_measurement(
    measurement: Optional[Dict[str, Any]],
    edge_index_by_id: Dict[int, int],
    channel_index: Dict[str, int],
) -> List[MeasurementReadout]:
    if not measurement:
        return []
    outputs = measurement.get("outputs") or []
    result: List[MeasurementReadout] = []
    for entry in outputs:
        name = str(entry["name"])
        edges_raw = entry.get("readout_edges") or []
        edges = tuple(edge_index_by_id[int(e_id)] for e_id in edges_raw)
        channels_raw = entry.get("channels")
        channels = None
        if channels_raw is not None:
            if not isinstance(channels_raw, Sequence) or isinstance(channels_raw, (str, bytes)):
                raise ValueError(f"E_MEASUREMENT_CHANNELS_FMT: {name}")
            channels = tuple(_resolve_channel_index(ch, channel_index) for ch in channels_raw)
        result.append(MeasurementReadout(name=name, edges=edges, channels=channels))
    return result


def _parse_coupling_rules(
    rules: Optional[Sequence[Dict[str, Any]]],
    channel_index: Dict[str, int],
    channels: Sequence[ChannelSpec],
    k: int,
) -> List[CouplingRule]:
    if not rules:
        return []
    result: List[CouplingRule] = []
    for rule in rules:
        name = str(rule.get("name", "unnamed_rule"))
        scope = rule.get("scope") or {}
        node_tags_any = _normalize_tags(scope.get("nodes_any"))
        out_edge_tags_any = _normalize_tags(scope.get("out_edges_any"))

        inputs_raw = rule.get("in") or []
        outputs_raw = rule.get("out") or []
        if not outputs_raw:
            raise ValueError(f"E_RULE_OUTPUT_EMPTY: {name}")

        inputs: List[RuleInput] = []
        for entry in inputs_raw:
            channel = _resolve_channel_index(entry["ch"], channel_index)
            minimum = int(entry.get("min", 1))
            if minimum != 1:
                raise ValueError(f"E_RULE_MIN_UNSUPPORTED: {name} requires min=1 (got {minimum})")
            inputs.append(
                RuleInput(
                    channel=channel,
                    minimum=minimum,
                    sum_over_phases=bool(entry.get("sum_over_phases", False)),
                )
            )

        outputs: List[RuleOutput] = []
        for entry in outputs_raw:
            channel = _resolve_channel_index(entry["ch"], channel_index)
            add = int(entry.get("add", 0))
            if add < 0:
                raise ValueError(f"E_RULE_OUTPUT_NEGATIVE: {name}")
            outputs.append(RuleOutput(channel=channel, add=add))

        phase_cfg = rule.get("phase") or {}
        phase_map: Dict[int, PhaseInstruction] = {}
        for ch_key, instr in phase_cfg.items():
            channel = _resolve_channel_index(ch_key, channel_index)
            phase_map[channel] = _parse_phase_instruction(
                instr,
                channel_index=channel_index,
                default_inputs=inputs,
                rule_name=name,
            )

        for output in outputs:
            if output.channel not in phase_map:
                phase_map[output.channel] = _default_phase_instruction(
                    output.channel,
                    inputs,
                    rule_name=name,
                )

        charge_in = sum(channels[inp.channel].charge * inp.minimum for inp in inputs)
        charge_out = sum(channels[out.channel].charge * out.add for out in outputs)
        charge_balance = charge_out - charge_in
        nonconservative = bool(rule.get("nonconservative", False))
        if charge_balance != 0 and not nonconservative:
            raise ValueError(f"E_RULE_CHARGE_IMBALANCE: {name}")

        result.append(
            CouplingRule(
                name=name,
                inputs=tuple(inputs),
                outputs=tuple(outputs),
                phase=phase_map,
                node_tags_any=node_tags_any if node_tags_any else None,
                out_edge_tags_any=out_edge_tags_any if out_edge_tags_any else None,
                nonconservative=nonconservative,
                charge_balance=charge_balance,
            )
        )
    return result


# --------------------------------------------------------------------------- #
# Utility helpers


def _normalize_tags(raw: Any) -> Tuple[str, ...]:
    if raw is None:
        return tuple()
    if isinstance(raw, str):
        return (raw,)
    if isinstance(raw, Sequence):
        tags = [str(item) for item in raw if item is not None]
        return tuple(sorted(set(tags)))
    return tuple()


def _resolve_channel_index(raw: Any, channel_index: Dict[str, int]) -> int:
    if isinstance(raw, int):
        if raw < 0 or raw >= len(channel_index):
            raise ValueError(f"E_CHANNEL_INDEX_RANGE: {raw}")
        return raw
    name = str(raw)
    if name not in channel_index:
        raise ValueError(f"E_CHANNEL_UNKNOWN: {name}")
    return channel_index[name]


def _resolve_edge_index(edge_id: int, directed_edges: Sequence[DirectedEdge]) -> int:
    for idx, edge in enumerate(directed_edges):
        if edge.id == edge_id:
            return idx
    raise KeyError(edge_id)


def _parse_phase_instruction(
    raw: Any,
    *,
    channel_index: Dict[str, int],
    default_inputs: Sequence[RuleInput],
    rule_name: str,
) -> PhaseInstruction:
    if isinstance(raw, str):
        if raw == "inherit":
            if len(default_inputs) != 1:
                raise ValueError(f"E_PHASE_INHERIT_AMBIGUOUS: {rule_name}")
            return PhaseInstruction(kind="inherit", sources=(default_inputs[0].channel,))
        if raw.startswith("inherit_from:"):
            name = raw.split(":", 1)[1]
            return PhaseInstruction(kind="inherit", sources=(_resolve_channel_index(name, channel_index),))
        if raw == "delta":
            return PhaseInstruction(kind="delta")
        if raw.startswith("fixed:"):
            value = int(raw.split(":", 1)[1])
            return PhaseInstruction(kind="fixed", value=value)
        raise ValueError(f"E_PHASE_UNKNOWN: {raw}")

    if isinstance(raw, dict) and "sum_from" in raw:
        sources = tuple(
            _resolve_channel_index(ch, channel_index) for ch in raw.get("sum_from", [])
        )
        if not sources:
            raise ValueError(f"E_PHASE_SUM_EMPTY: {rule_name}")
        return PhaseInstruction(kind="sum", sources=sources)

    raise ValueError(f"E_PHASE_INVALID: {raw}")


def _default_phase_instruction(
    channel: int,
    inputs: Sequence[RuleInput],
    rule_name: str,
) -> PhaseInstruction:
    matching = [inp for inp in inputs if inp.channel == channel]
    if len(matching) == 1:
        return PhaseInstruction(kind="inherit", sources=(matching[0].channel,))
    if not matching:
        return PhaseInstruction(kind="delta")
    raise ValueError(f"E_PHASE_DEFAULT_AMBIGUOUS: {rule_name}")


def _validate_mask_value(value: Any) -> int:
    ivalue = int(value)
    if ivalue not in (0, 1):
        raise ValueError("E_FUSION_MASK_VAL")
    return ivalue


