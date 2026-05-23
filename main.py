"""
UMG Block Library MCP Server — v0.1 Runtime Core
Universal Modular Generation — cognitive sleeve compiler and runtime inspector

Tools:
  compile_sleeve      — compile a governed sleeve from plain language intent
  inspect_active_state — given sleeve + context, show what's on/off and why
  generate_molt_map   — MOLT authority chain view (what is the AI doing right now)
  generate_ir_graph   — routing graph (how did the system get here)
  explain_route       — human-readable routing explanation
  search_blocks       — search the 1,400-block canonical library
  audit_sleeve        — validate a sleeve against the canonical registry
  get_block_types     — overview of all 8 MOLT block types
  umg_preview_gate_eval — Phase 2a gate + vertical hierarchy preview

Sovereign: NeoMAG  |  License: Apache 2.0  |  Version: 0.2.0-preview
"""

import json
import os
import re
import time
from copy import deepcopy

try:
    from mcp.server.fastmcp import FastMCP
except ModuleNotFoundError:  # pragma: no cover - lightweight test fallback
    class FastMCP:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

        def tool(self):
            def decorator(fn):
                return fn
            return decorator

        def run(self, *args, **kwargs):
            raise RuntimeError("FastMCP runtime unavailable in this Python environment")

# ── LOAD BLOCK LIBRARY ───────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "blocks.json")) as f:
    LIBRARY = json.load(f)

NAME_IDX = {
    t: {b["name"]: b for b in blocks}
    for t, blocks in LIBRARY.items()
}
ALL_BLOCKS = [b for blocks in LIBRARY.values() for b in blocks]
TOTAL = sum(len(v) for v in LIBRARY.values())

# ── MOLT AUTHORITY HIERARCHY ─────────────────────────────────────────────────
# Lower rank = higher authority. DIRECTIVE governs everything below it.
AUTHORITY_RANK = {
    "TRIGGER": 0,
    "DIRECTIVE": 1,
    "INSTRUCTION": 2,
    "SUBJECT": 3,
    "PRIMARY": 4,
    "PHILOSOPHY": 5,
    "BLUEPRINT": 6,
    "PERSONA": 7,
}

TYPE_DESCRIPTIONS = {
    "TRIGGER": "Gates - activation conditions that open a cognitive path. Never used inside NeoBlocks.",
    "DIRECTIVE": "Authority - strategic behavioral overlay and scope. Governs all blocks below it.",
    "INSTRUCTION": "Method - procedural logic and execution approach.",
    "SUBJECT": "Target - domains, data entities, and objects of cognition.",
    "PRIMARY": "Outcome - core values and results being driven.",
    "PHILOSOPHY": "Worldview - ethical lens and decision framework.",
    "BLUEPRINT": "Structure - output format, schema, and form.",
    "PERSONA": "Voice - communication style and relational mode.",
}

COMPILATION_RULES = """
UMG COMPILATION RULES (follow exactly):

STRUCTURE:
- Sleeve: 1-3 NeoStacks
- NeoStack: 1-3 NeoBlocks + optional TRIGGER gates (0-2)
- NeoBlock: 2-5 blocks from non-TRIGGER types only
- TRIGGER blocks go in NeoStack gates[] ONLY - never inside NeoBlocks
- Each NeoBlock should mix at least 2 different block types

AUTHORITY ORDER within NeoBlocks (apply top-down):
  DIRECTIVE (1) → INSTRUCTION (2) → SUBJECT (3) → PRIMARY (4)
  → PHILOSOPHY (5) → BLUEPRINT (6) → PERSONA (7)

NAMING: Use EXACT canonical block names from the library provided.
No fabrication - if a concept doesn't exist, flag it as custom.

OUTPUT FORMAT (governed sleeve JSON):
{
  "sleeve_name": "...",
  "reasoning": "brief design rationale",
  "provenance": {
    "sourceMode": "compiled_by_claude",
    "routePurity": "unverified",
    "sovereignReviewRequired": true
  },
  "neoStacks": [
    {
      "name": "...",
      "gates": [{"type": "TRIGGER", "name": "exact canonical name"}],
      "neoBlocks": [
        {
          "name": "...",
          "blocks": [
            {"type": "DIRECTIVE", "name": "exact canonical name"},
            {"type": "INSTRUCTION", "name": "exact canonical name"},
            {"type": "PRIMARY", "name": "exact canonical name"}
          ]
        }
      ]
    }
  ]
}
"""


# ── PHASE 2A HELPERS ─────────────────────────────────────────────────────────
def _normalize_signal_name(value: str) -> str:
    return str(value or "").strip().lower()


def _active_signal_set(active_context) -> set[str]:
    if active_context is None:
        return set()
    if isinstance(active_context, dict):
        signals = active_context.get("signals", [])
    else:
        signals = active_context
    return {_normalize_signal_name(s) for s in signals if _normalize_signal_name(s)}


def _make_trace_entry(pass_name: str, step_index: int, target_id: str | None, result: str, reason: str, inputs: dict) -> dict:
    return {
        "pass": pass_name,
        "step_index": step_index,
        "target_id": target_id,
        "result": result,
        "reason": reason,
        "inputs": inputs,
    }


def _make_runtime_seed(sleeve: dict, active_context) -> dict:
    return {
        "runtime_id": f"RT-{int(time.time())}",
        "sleeve_id": sleeve.get("id", sleeve.get("sleeve_id", "unknown")),
        "sleeve_name": sleeve.get("name", sleeve.get("sleeve_name", "unnamed")),
        "source_mode": sleeve.get("provenance", {}).get("sourceMode", "unknown"),
        "active_context": {
            "signals": sorted(_active_signal_set(active_context)),
            "raw": deepcopy(active_context) if active_context is not None else [],
        },
        "turn_index": 1,
        "previous_runtime_id": None,
        "stateful_features_enabled": False,
        "gate_evaluations": [],
        "active_stacks": [],
        "suppressed_items": [],
        "active_blocks": [],
        "conflicts": [],
        "warnings": [],
        "route_trace": [],
    }


def _stack_id(ns: dict, idx: int) -> str:
    return ns.get("id") or f"NS-{idx + 1}"


def _block_id(block: dict, ns_id: str, nb_id: str, idx: int) -> str:
    return block.get("id") or f"{ns_id}:{nb_id}:BLK-{idx + 1}"


def _neoblock_id(nb: dict, ns_id: str, idx: int) -> str:
    return nb.get("id") or f"{ns_id}:NB-{idx + 1}"


def _default_gate_for_stack(ns: dict, idx: int) -> dict:
    stack_id = _stack_id(ns, idx)
    return {
        "gate_id": f"GATE_ALWAYS_ON_{stack_id}",
        "operator": "fallback",
        "fallback": True,
        "priority": 0,
        "target_stack_id": stack_id,
        "description": "No gate provided - stack defaults to always-on behavior in legacy mode.",
        "_legacy_no_gate": True,
    }


# ── PHASE 2A: GATE ENGINE ────────────────────────────────────────────────────
def evaluate_gates(runtime_spec: dict, sleeve: dict, active_context) -> dict:
    """
    Evaluate all NeoStack gate expressions and update RuntimeSpec.

    Exact signature required for Phase 2a.

    Output fields populated:
    - runtime_spec["gate_evaluations"]: list[GateEvaluationResult]
    - runtime_spec["active_stacks"]: list[{stack_id, stack_name, gate_id, priority}]
    - runtime_spec["suppressed_items"]: appended stack suppression records
    - runtime_spec["route_trace"]: gate_evaluation pass entries
    """
    signals = _active_signal_set(active_context)
    step_index = len(runtime_spec["route_trace"])
    evaluations = []
    non_fallback_matches = []
    fallback_pending = []

    for ns_idx, ns in enumerate(sleeve.get("neoStacks", [])):
        stack_id = _stack_id(ns, ns_idx)
        stack_name = ns.get("name", stack_id)
        gates = ns.get("gates", []) or [_default_gate_for_stack(ns, ns_idx)]

        for gate in gates:
            gate_id = gate.get("gate_id") or gate.get("id") or gate.get("name") or f"GATE_{stack_id}"
            operator = gate.get("operator", "any")
            conditions = gate.get("conditions", []) or []
            negated_conditions = [
                _normalize_signal_name(s) for s in gate.get("negated_conditions", []) if _normalize_signal_name(s)
            ]
            matched_conditions = []
            failed_conditions = []
            score = None
            threshold = gate.get("threshold")
            matched = False
            result = "suppressed"
            reason = ""
            priority = int(gate.get("priority", 50))

            if operator == "fallback" or gate.get("fallback") is True:
                fallback_pending.append((ns, gate, stack_id, stack_name))
                continue

            if operator == "priority":
                matched = True
                result = "activated"
                reason = f"Priority gate applied with priority {priority}."
            else:
                condition_signals = [_normalize_signal_name(c.get("signal")) for c in conditions if _normalize_signal_name(c.get("signal"))]
                matched_conditions = [s for s in condition_signals if s in signals]
                failed_conditions = [s for s in condition_signals if s not in signals]
                negated_present = [s for s in negated_conditions if s in signals]

                if operator == "any":
                    matched = len(matched_conditions) >= 1 and not negated_present
                    reason = (
                        f"Matched {len(matched_conditions)} of {len(condition_signals)} required condition(s)."
                        if matched else
                        f"No condition matched." if not matched_conditions else
                        f"Negated condition present: {', '.join(negated_present)}."
                    )
                elif operator == "all":
                    matched = len(condition_signals) > 0 and len(failed_conditions) == 0 and not negated_present
                    reason = (
                        "All conditions matched."
                        if matched else
                        f"Missing required conditions: {', '.join(failed_conditions)}."
                        if failed_conditions else
                        f"Negated condition present: {', '.join(negated_present)}."
                    )
                elif operator == "not":
                    required_ok = len(condition_signals) == 0 or len(failed_conditions) == 0
                    matched = required_ok and len(negated_present) == 0
                    reason = (
                        "Negated conditions absent and required conditions matched."
                        if matched and condition_signals else
                        "Negated conditions absent."
                        if matched else
                        f"Negated condition present: {', '.join(negated_present)}."
                        if negated_present else
                        f"Missing required conditions: {', '.join(failed_conditions)}."
                    )
                elif operator == "threshold":
                    score = round(sum(float(c.get("gate_weight", 1.0)) for c in conditions
                                      if _normalize_signal_name(c.get("signal")) in signals), 6)
                    threshold = float(threshold if threshold is not None else 1.0)
                    matched = score >= threshold and len(negated_present) == 0
                    reason = (
                        f"Threshold score {score:.2f} met required {threshold:.2f}."
                        if matched else
                        f"Threshold score {score:.2f} below required {threshold:.2f}."
                        if len(negated_present) == 0 else
                        f"Negated condition present: {', '.join(negated_present)}."
                    )
                else:
                    matched = False
                    failed_conditions = condition_signals
                    reason = f"Unsupported gate operator '{operator}'."
                    runtime_spec["warnings"].append({
                        "warning_type": "sovereign_review_recommended",
                        "block_ids": [gate_id],
                        "reason": reason,
                    })

                result = "activated" if matched else "suppressed"

            evaluation = {
                "gate_id": gate_id,
                "target_stack_id": stack_id,
                "operator": operator,
                "matched": matched,
                "score": score,
                "threshold": threshold if operator == "threshold" else None,
                "matched_conditions": matched_conditions,
                "failed_conditions": failed_conditions,
                "result": result,
                "reason": reason,
                "priority": priority,
                "stack_name": stack_name,
            }
            evaluations.append(evaluation)
            runtime_spec["route_trace"].append(_make_trace_entry(
                "gate_evaluation",
                step_index,
                stack_id,
                result,
                reason,
                {
                    "gate_id": gate_id,
                    "operator": operator,
                    "priority": priority,
                    "signals": sorted(signals),
                    "matched_conditions": matched_conditions,
                    "failed_conditions": failed_conditions,
                    "score": score,
                    "threshold": threshold if operator == "threshold" else None,
                },
            ))
            step_index += 1

            if matched:
                non_fallback_matches.append((priority, ns_idx, ns, gate, evaluation))
            else:
                suppression_reason = "gate_score_below_threshold" if operator == "threshold" and score is not None else "trigger_mismatch"
                runtime_spec["suppressed_items"].append({
                    "id": stack_id,
                    "suppression_reason": suppression_reason,
                    "suppressed_by_id": gate_id,
                    "reason": reason,
                })

    if non_fallback_matches:
        non_fallback_matches.sort(key=lambda item: (-item[0], item[1]))
        for priority, _ns_idx, ns, gate, evaluation in non_fallback_matches:
            runtime_spec["active_stacks"].append({
                "stack_id": evaluation["target_stack_id"],
                "stack_name": ns.get("name", evaluation["target_stack_id"]),
                "gate_id": evaluation["gate_id"],
                "priority": priority,
            })
    else:
        for ns, gate, stack_id, stack_name in fallback_pending:
            gate_id = gate.get("gate_id") or f"GATE_FALLBACK_{stack_id}"
            priority = int(gate.get("priority", 0))
            reason = "No gate matched - fallback activated."
            evaluation = {
                "gate_id": gate_id,
                "target_stack_id": stack_id,
                "operator": "fallback",
                "matched": True,
                "score": None,
                "threshold": None,
                "matched_conditions": [],
                "failed_conditions": [],
                "result": "fallback_activated",
                "reason": reason,
                "priority": priority,
                "stack_name": stack_name,
            }
            evaluations.append(evaluation)
            runtime_spec["active_stacks"].append({
                "stack_id": stack_id,
                "stack_name": stack_name,
                "gate_id": gate_id,
                "priority": priority,
            })
            runtime_spec["route_trace"].append(_make_trace_entry(
                "gate_evaluation",
                step_index,
                stack_id,
                "fallback_activated",
                reason,
                {
                    "gate_id": gate_id,
                    "operator": "fallback",
                    "priority": priority,
                    "signals": sorted(signals),
                    "matched_conditions": [],
                    "failed_conditions": [],
                    "score": None,
                    "threshold": None,
                },
            ))
            step_index += 1

    runtime_spec["gate_evaluations"] = evaluations
    return runtime_spec


# ── PHASE 2A: VERTICAL HIERARCHY ─────────────────────────────────────────────
def resolve_vertical_hierarchy(runtime_spec: dict, sleeve: dict) -> dict:
    """
    Resolve active content by vertical authority rank after gate activation.

    Exact signature required for Phase 2a.

    Output fields populated:
    - runtime_spec["active_blocks"]
    - runtime_spec["vertical_resolution"]
    - runtime_spec["conflicts"]
    - runtime_spec["suppressed_items"] additions for lower-authority content
    - runtime_spec["route_trace"] vertical_resolution pass entries
    """
    step_index = len(runtime_spec["route_trace"])
    active_stack_ids = {s["stack_id"] for s in runtime_spec.get("active_stacks", [])}
    candidate_blocks = []
    stack_lookup = {}

    for ns_idx, ns in enumerate(sleeve.get("neoStacks", [])):
        stack_id = _stack_id(ns, ns_idx)
        if stack_id not in active_stack_ids:
            continue
        stack_lookup[stack_id] = ns
        for nb_idx, nb in enumerate(ns.get("neoBlocks", [])):
            nb_id = _neoblock_id(nb, stack_id, nb_idx)
            blocks = sorted(nb.get("blocks", []), key=lambda b: AUTHORITY_RANK.get(b.get("type", ""), 99))
            for blk_idx, block in enumerate(blocks):
                molt_type = block.get("type", "")
                authority_rank = AUTHORITY_RANK.get(molt_type, 99)
                candidate_blocks.append({
                    "block_id": _block_id(block, stack_id, nb_id, blk_idx),
                    "block_name": block.get("name", ""),
                    "molt_type": molt_type,
                    "authority_rank": authority_rank,
                    "neoblock_id": nb_id,
                    "neostack_id": stack_id,
                    "source": "library" if block.get("name") in NAME_IDX.get(molt_type, {}) else "candidate",
                    "stack_priority": next((s["priority"] for s in runtime_spec["active_stacks"] if s["stack_id"] == stack_id), 0),
                })

    candidate_blocks.sort(key=lambda b: (b["authority_rank"], -b["stack_priority"], b["block_id"]))
    active_blocks = []
    suppressed = []
    dominant_per_type = {}

    for block in candidate_blocks:
        key = block["molt_type"]
        if key not in dominant_per_type:
            dominant_per_type[key] = block["block_id"]
            active_blocks.append({k: block[k] for k in [
                "block_id", "block_name", "molt_type", "authority_rank", "neoblock_id", "neostack_id", "source"
            ]})
            runtime_spec["route_trace"].append(_make_trace_entry(
                "vertical_resolution",
                step_index,
                block["block_id"],
                "active",
                f"{block['molt_type']} block retained as dominant active block for this authority type.",
                {
                    "molt_type": block["molt_type"],
                    "authority_rank": block["authority_rank"],
                    "neostack_id": block["neostack_id"],
                    "stack_priority": block["stack_priority"],
                },
            ))
            step_index += 1
        else:
            winner_id = dominant_per_type[key]
            suppressed_reason = "higher_vertical_authority"
            reason = f"Suppressed by dominant {key} block {winner_id}."
            suppressed.append({
                "id": block["block_id"],
                "suppression_reason": suppressed_reason,
                "suppressed_by_id": winner_id,
                "reason": reason,
            })
            runtime_spec["conflicts"].append({
                "conflict_id": f"CONF-{winner_id}-{block['block_id']}",
                "involved_ids": [winner_id, block["block_id"]],
                "conflict_type": "authority_conflict",
                "resolution_status": "suppressed_lower",
                "winner_id": winner_id,
                "reason": reason,
            })
            runtime_spec["route_trace"].append(_make_trace_entry(
                "vertical_resolution",
                step_index,
                block["block_id"],
                "suppressed",
                reason,
                {
                    "molt_type": block["molt_type"],
                    "authority_rank": block["authority_rank"],
                    "neostack_id": block["neostack_id"],
                    "suppressed_by_id": winner_id,
                    "stack_priority": block["stack_priority"],
                },
            ))
            step_index += 1

    runtime_spec["active_blocks"] = active_blocks
    runtime_spec["suppressed_items"].extend(suppressed)
    runtime_spec["vertical_resolution"] = {
        "dominant_block_ids": dominant_per_type,
        "active_block_count": len(active_blocks),
        "suppressed_block_count": len(suppressed),
        "resolution_mode": "rank_then_priority",
    }
    return runtime_spec


# ── LEGACY HELPERS ────────────────────────────────────────────────────────────
def _match_context(gate_name: str, active_context: list) -> bool:
    """Check if a trigger gate matches the active context."""
    gate_lower = gate_name.lower()
    for ctx in active_context:
        ctx_lower = ctx.lower()
        if gate_lower == ctx_lower:
            return True
        if gate_lower in ctx_lower or ctx_lower in gate_lower:
            return True
        gate_words = set(gate_lower.split())
        ctx_words = set(ctx_lower.split())
        if len(gate_words & ctx_words) >= 2:
            return True
    return False


def _generate_warnings(active_blocks: list, suppressed_blocks: list) -> list:
    warnings = []
    active_types = {b.get("type") for b in active_blocks}

    if "DIRECTIVE" not in active_types and active_blocks:
        warnings.append("No active DIRECTIVE block — cognitive authority anchor missing")
    if "INSTRUCTION" not in active_types and active_blocks:
        warnings.append("No active INSTRUCTION block — execution method undefined")
    if "PRIMARY" not in active_types and active_blocks:
        warnings.append("No active PRIMARY block — outcome anchor missing")
    if len(active_blocks) == 0:
        warnings.append("No active blocks — all NeoStacks suppressed. Check active_context triggers.")
    if suppressed_blocks and not active_blocks:
        warnings.append(
            f"{len(suppressed_blocks)} block(s) suppressed with nothing active — no trigger matched any NeoStack gate"
        )
    return warnings


def _build_molt_map(active_blocks: list, suppressed_blocks: list, trigger_evaluations: list) -> dict:
    active_trigger = next(
        (e["matched"][0] for e in trigger_evaluations if e.get("result") == "active" and e.get("matched")),
        "no trigger matched"
    )
    active_neostack = next(
        (e["neostack"] for e in trigger_evaluations if e.get("result") == "active"),
        "none"
    )

    by_type = {}
    for btype in ["DIRECTIVE", "INSTRUCTION", "SUBJECT", "PRIMARY", "PHILOSOPHY", "BLUEPRINT", "PERSONA"]:
        by_type[btype] = [
            {
                "id": b.get("id", ""),
                "name": b.get("name", ""),
                "neoblock": b.get("_neoblock", ""),
                "neostack": b.get("_neostack", ""),
                "state": "active"
            }
            for b in active_blocks if b.get("type") == btype
        ]

    dominant_directive = by_type["DIRECTIVE"][0]["name"] if by_type["DIRECTIVE"] else None

    suppressed_view = [
        {
            "id": b.get("id", ""),
            "type": b.get("type", ""),
            "name": b.get("name", ""),
            "neoblock": b.get("_neoblock", ""),
            "state": "suppressed",
            "reason": b.get("_reason", "parent stack suppressed")
        }
        for b in suppressed_blocks
    ]

    return {
        "active_trigger": active_trigger,
        "active_neostack": active_neostack,
        "dominant_directive": dominant_directive,
        "authority_chain": by_type,
        "suppressed": suppressed_view,
        "off": [],
        "cognitive_summary": (
            f"Directive: {dominant_directive or 'none'} | "
            f"Instructions: {len(by_type['INSTRUCTION'])} active | "
            f"Subject: {', '.join(b['name'] for b in by_type['SUBJECT']) or 'none'} | "
            f"Primary: {', '.join(b['name'] for b in by_type['PRIMARY'][:2]) or 'none'}"
        )
    }


def _build_ir_graph(sleeve: dict, active_neostacks: list, suppressed_neostacks: list) -> dict:
    nodes = []
    edges = []
    active_route = []
    suppressed_routes = []

    sleeve_id = sleeve.get("id", sleeve.get("sleeve_id", "SL-unknown"))
    sleeve_name = sleeve.get("name", sleeve.get("sleeve_name", "unnamed"))

    nodes.append({
        "id": sleeve_id,
        "type": "sleeve",
        "label": sleeve_name,
        "state": "active",
        "authority_rank": None,
        "source_ref": sleeve_id
    })
    active_route.append(sleeve_id)

    for ns in active_neostacks:
        ns_id = ns.get("id", f"NS-{ns['name']}")
        nodes.append({
            "id": ns_id,
            "type": "neostack",
            "label": ns["name"],
            "state": "active",
            "authority_rank": None,
            "source_ref": ns_id
        })
        edges.append({
            "from": sleeve_id,
            "to": ns_id,
            "type": "contains",
            "state": "active",
            "reason": "sleeve contains this NeoStack"
        })
        active_route.append(ns_id)

        for gate in ns.get("gates", []):
            gate_id = gate.get("id", f"TRG-{gate.get('name','').replace(' ','-')}")
            nodes.append({
                "id": gate_id,
                "type": "trigger_gate",
                "label": gate.get("name", ""),
                "state": "active",
                "authority_rank": 0,
                "source_ref": gate_id
            })
            edges.append({
                "from": gate_id,
                "to": ns_id,
                "type": "activates",
                "state": "active",
                "reason": "trigger gate matched - activates NeoStack"
            })

        for nb in ns.get("_neoblocks", ns.get("neoBlocks", [])):
            nb_id = nb.get("id", f"NB-{nb['name']}")
            nodes.append({
                "id": nb_id,
                "type": "neoblock",
                "label": nb["name"],
                "state": "active",
                "authority_rank": None,
                "source_ref": nb_id
            })
            edges.append({
                "from": ns_id,
                "to": nb_id,
                "type": "routes_to",
                "state": "active",
                "reason": "NeoStack routes to NeoBlock"
            })
            active_route.append(nb_id)

            blocks = nb.get("_blocks_by_authority", nb.get("blocks", []))
            blocks_sorted = sorted(blocks, key=lambda b: AUTHORITY_RANK.get(b.get("type", ""), 99))
            for block in blocks_sorted:
                b_id = block.get("id", f"{block.get('type','B')}-{block.get('name','').replace(' ','-')}")
                nodes.append({
                    "id": b_id,
                    "type": "molt_block",
                    "label": f"[{block.get('type','')}] {block.get('name','')}",
                    "state": "active",
                    "authority_rank": AUTHORITY_RANK.get(block.get("type", ""), 99),
                    "source_ref": b_id
                })
                edges.append({
                    "from": nb_id,
                    "to": b_id,
                    "type": "contains",
                    "state": "active",
                    "reason": f"authority rank {AUTHORITY_RANK.get(block.get('type',''),99)}"
                })
                active_route.append(b_id)

    for ns in suppressed_neostacks:
        ns_id = ns.get("id", f"NS-{ns['name']}")
        suppressed_path = [ns_id]
        nodes.append({
            "id": ns_id,
            "type": "neostack",
            "label": ns["name"],
            "state": "suppressed",
            "authority_rank": None,
            "source_ref": ns_id
        })
        edges.append({
            "from": sleeve_id,
            "to": ns_id,
            "type": "contains",
            "state": "suppressed",
            "reason": "NeoStack suppressed - trigger gate not matched"
        })

        for gate in ns.get("gates", []):
            gate_id = gate.get("id", f"TRG-{gate.get('name','').replace(' ','-')}")
            nodes.append({
                "id": gate_id,
                "type": "trigger_gate",
                "label": gate.get("name", ""),
                "state": "inactive",
                "authority_rank": 0,
                "source_ref": gate_id
            })
            edges.append({
                "from": gate_id,
                "to": ns_id,
                "type": "suppresses",
                "state": "inactive",
                "reason": "trigger gate not matched - NeoStack suppressed"
            })
            suppressed_path.append(gate_id)

        for nb in ns.get("_neoblocks", ns.get("neoBlocks", [])):
            nb_id = nb.get("id", f"NB-{nb['name']}")
            nodes.append({
                "id": nb_id,
                "type": "neoblock",
                "label": nb["name"],
                "state": "suppressed",
                "authority_rank": None,
                "source_ref": nb_id
            })
            edges.append({
                "from": ns_id,
                "to": nb_id,
                "type": "routes_to",
                "state": "suppressed",
                "reason": "suppressed by parent NeoStack"
            })
            suppressed_path.append(nb_id)

            for block in nb.get("blocks", []):
                b_id = block.get("id", f"{block.get('type','B')}-{block.get('name','').replace(' ','-')}")
                nodes.append({
                    "id": b_id,
                    "type": "molt_block",
                    "label": f"[{block.get('type','')}] {block.get('name','')}",
                    "state": "suppressed",
                    "authority_rank": AUTHORITY_RANK.get(block.get("type", ""), 99),
                    "source_ref": b_id
                })
                edges.append({
                    "from": nb_id,
                    "to": b_id,
                    "type": "contains",
                    "state": "suppressed",
                    "reason": "suppressed by parent chain"
                })
                suppressed_path.append(b_id)

        suppressed_routes.append(suppressed_path)

    return {
        "nodes": nodes,
        "edges": edges,
        "active_route": active_route,
        "suppressed_routes": suppressed_routes,
        "conflicts": [],
        "warnings": [],
        "node_counts": {
            "total": len(nodes),
            "active": sum(1 for n in nodes if n["state"] == "active"),
            "suppressed": sum(1 for n in nodes if n["state"] == "suppressed"),
            "inactive": sum(1 for n in nodes if n["state"] == "inactive"),
        }
    }


def _build_runtime_spec(sleeve: dict, active_context: list) -> dict:
    active_context_safe = active_context if active_context else []

    active_neostacks = []
    suppressed_neostacks = []
    trigger_evaluations = []

    for ns in sleeve.get("neoStacks", []):
        gates = ns.get("gates", [])

        if not gates:
            ns_state = "active"
            eval_entry = {
                "neostack": ns.get("name", ""),
                "gates": [],
                "matched": [],
                "result": "active",
                "reason": "no gate - always active"
            }
        else:
            matched = [g.get("name", "") for g in gates if _match_context(g.get("name", ""), active_context_safe)]
            unmatched = [g.get("name", "") for g in gates if not _match_context(g.get("name", ""), active_context_safe)]

            if matched:
                ns_state = "active"
                eval_entry = {
                    "neostack": ns.get("name", ""),
                    "gates": [g.get("name") for g in gates],
                    "matched": matched,
                    "unmatched": unmatched,
                    "result": "active",
                    "reason": f"gate matched: {', '.join(matched)}"
                }
            else:
                ns_state = "suppressed"
                eval_entry = {
                    "neostack": ns.get("name", ""),
                    "gates": [g.get("name") for g in gates],
                    "matched": [],
                    "unmatched": unmatched,
                    "result": "suppressed",
                    "reason": f"no gate matched (requires: {', '.join(unmatched)})"
                }

        trigger_evaluations.append(eval_entry)

        resolved_neoblocks = []
        for nb in ns.get("neoBlocks", []):
            blocks_sorted = sorted(nb.get("blocks", []), key=lambda b: AUTHORITY_RANK.get(b.get("type", ""), 99))
            resolved_neoblocks.append({
                **nb,
                "_state": ns_state,
                "_blocks_by_authority": blocks_sorted
            })

        ns_resolved = {**ns, "_state": ns_state, "_neoblocks": resolved_neoblocks}

        if ns_state == "active":
            active_neostacks.append(ns_resolved)
        else:
            suppressed_neostacks.append(ns_resolved)

    active_blocks = []
    for ns in active_neostacks:
        for nb in ns["_neoblocks"]:
            for b in nb["_blocks_by_authority"]:
                active_blocks.append({
                    **b,
                    "_neoblock": nb.get("name", ""),
                    "_neostack": ns.get("name", ""),
                    "_state": "active",
                    "_authority_rank": AUTHORITY_RANK.get(b.get("type", ""), 99)
                })

    suppressed_blocks = []
    for ns in suppressed_neostacks:
        reason = next((e["reason"] for e in trigger_evaluations if e["neostack"] == ns.get("name", "")), "parent stack suppressed")
        for nb in ns.get("_neoblocks", []):
            for b in nb.get("_blocks_by_authority", nb.get("blocks", [])):
                suppressed_blocks.append({
                    **b,
                    "_neoblock": nb.get("name", ""),
                    "_neostack": ns.get("name", ""),
                    "_state": "suppressed",
                    "_reason": reason,
                    "_authority_rank": AUTHORITY_RANK.get(b.get("type", ""), 99)
                })

    authority_order = sorted(active_blocks, key=lambda b: b["_authority_rank"])
    dominant_directive = next((b for b in authority_order if b.get("type") == "DIRECTIVE"), None)

    molt_map = _build_molt_map(active_blocks, suppressed_blocks, trigger_evaluations)
    ir_graph = _build_ir_graph(sleeve, active_neostacks, suppressed_neostacks)
    warnings = _generate_warnings(active_blocks, suppressed_blocks)

    return {
        "runtime_id": f"RT-{int(time.time())}",
        "sleeve_id": sleeve.get("id", sleeve.get("sleeve_id", "unknown")),
        "sleeve_name": sleeve.get("name", sleeve.get("sleeve_name", "unnamed")),
        "source_mode": sleeve.get("provenance", {}).get("sourceMode", "unknown"),
        "route_purity": "clean_native" if not any(b.get("custom") for b in active_blocks) else "mixed",
        "active_context": active_context_safe,
        "trigger_evaluations": trigger_evaluations,
        "active_neostacks": [{"id": ns.get("id", ""), "name": ns.get("name", "")} for ns in active_neostacks],
        "suppressed_neostacks": [
            {
                "id": ns.get("id", ""),
                "name": ns.get("name", ""),
                "reason": next((e["reason"] for e in trigger_evaluations if e["neostack"] == ns.get("name", "")), "")
            }
            for ns in suppressed_neostacks
        ],
        "active_blocks_count": len(active_blocks),
        "suppressed_blocks_count": len(suppressed_blocks),
        "total_neostacks": len(sleeve.get("neoStacks", [])),
        "dominant_directive": dominant_directive.get("name") if dominant_directive else None,
        "authority_order": [
            {
                "id": b.get("id", ""),
                "type": b.get("type", ""),
                "name": b.get("name", ""),
                "neoblock": b.get("_neoblock", ""),
                "neostack": b.get("_neostack", ""),
                "authority_rank": b.get("_authority_rank", 99)
            }
            for b in authority_order
        ],
        "suppressed_blocks_detail": [
            {
                "id": b.get("id", ""),
                "type": b.get("type", ""),
                "name": b.get("name", ""),
                "neoblock": b.get("_neoblock", ""),
                "neostack": b.get("_neostack", ""),
                "reason": b.get("_reason", "")
            }
            for b in suppressed_blocks
        ],
        "conflicts": [],
        "warnings": warnings,
        "molt_map": molt_map,
        "ir_graph": ir_graph
    }


def _run_phase2a_preview(sleeve: dict, active_context) -> dict:
    runtime_spec = _make_runtime_seed(sleeve, active_context)
    runtime_spec = evaluate_gates(runtime_spec, sleeve, active_context)
    runtime_spec = resolve_vertical_hierarchy(runtime_spec, sleeve)
    return runtime_spec


# ── MCP SERVER ────────────────────────────────────────────────────────────────
mcp = FastMCP(
    "UMG Block Library",
    json_response=True,
    instructions=(
        "You are connected to the UMG (Universal Modular Generation) runtime. "
        "UMG structures AI cognition into typed MOLT blocks assembled into governed sleeves. "
        "MOLT authority hierarchy: DIRECTIVE → INSTRUCTION → SUBJECT → PRIMARY → PHILOSOPHY → BLUEPRINT → PERSONA. "
        "Use compile_sleeve to build a sleeve. "
        "Use inspect_active_state, generate_molt_map, or generate_ir_graph to inspect runtime state. "
        "Use explain_route for human-readable routing explanation. "
        "Use umg_preview_gate_eval for v0.2 Phase 2a gate and vertical-hierarchy preview. "
        "All compiled sleeves require sovereign (NeoMAG) review before ClawHub deployment."
    )
)


@mcp.tool()
def compile_sleeve(intent: str, active_context: list[str] = None) -> dict:
    library_summary = {
        btype: {
            "count": len(blocks),
            "description": TYPE_DESCRIPTIONS[btype],
            "authority_rank": AUTHORITY_RANK.get(btype, 99),
            "blocks": [{"id": b["id"], "name": b["name"]} for b in blocks]
        }
        for btype, blocks in LIBRARY.items()
    }

    return {
        "intent": intent,
        "instruction": (
            "Compile a governed UMG sleeve for the intent above. "
            "Follow the compilation rules exactly. "
            "Use ONLY canonical block names from the library provided. "
            "Order blocks within each NeoBlock by MOLT authority rank (DIRECTIVE first). "
            "Return a complete governed sleeve JSON."
        ),
        "compilation_rules": COMPILATION_RULES,
        "molt_authority_hierarchy": AUTHORITY_RANK,
        "canonical_library": library_summary,
        "total_blocks": TOTAL,
        "active_context_hint": active_context or [],
        "sovereign": "NeoMAG",
        "license": "Apache-2.0"
    }


@mcp.tool()
def inspect_active_state(sleeve_json: str, active_context: list[str] = None) -> dict:
    try:
        sleeve = json.loads(sleeve_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}

    return _build_runtime_spec(sleeve, active_context or [])


@mcp.tool()
def generate_molt_map(sleeve_json: str, active_context: list[str] = None) -> dict:
    try:
        sleeve = json.loads(sleeve_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}

    spec = _build_runtime_spec(sleeve, active_context or [])
    return {
        "sleeve_name": spec["sleeve_name"],
        "runtime_id": spec["runtime_id"],
        "active_context": spec["active_context"],
        "warnings": spec["warnings"],
        **spec["molt_map"]
    }


@mcp.tool()
def generate_ir_graph(sleeve_json: str, active_context: list[str] = None) -> dict:
    try:
        sleeve = json.loads(sleeve_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}

    spec = _build_runtime_spec(sleeve, active_context or [])
    return {
        "sleeve_name": spec["sleeve_name"],
        "runtime_id": spec["runtime_id"],
        "active_context": spec["active_context"],
        "route_purity": spec["route_purity"],
        "trigger_evaluations": spec["trigger_evaluations"],
        **spec["ir_graph"]
    }


@mcp.tool()
def explain_route(sleeve_json: str, active_context: list[str] = None) -> dict:
    try:
        sleeve = json.loads(sleeve_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}

    spec = _build_runtime_spec(sleeve, active_context or [])
    mm = spec["molt_map"]

    lines = []
    lines.append(f"SLEEVE: {spec['sleeve_name']}")
    lines.append(f"CONTEXT: {', '.join(spec['active_context']) or 'none provided'}")
    lines.append("")

    if spec["active_neostacks"]:
        lines.append(f"ACTIVE NEOSTACKS ({len(spec['active_neostacks'])}):")
        for ns in spec["active_neostacks"]:
            ev = next((e for e in spec["trigger_evaluations"] if e["neostack"] == ns["name"]), {})
            lines.append(f"  ✓ {ns['name']} — {ev.get('reason', 'active')}")
    else:
        lines.append("ACTIVE NEOSTACKS: none — no triggers matched")

    lines.append("")

    if spec["suppressed_neostacks"]:
        lines.append(f"SUPPRESSED NEOSTACKS ({len(spec['suppressed_neostacks'])}):")
        for ns in spec["suppressed_neostacks"]:
            lines.append(f"  ✗ {ns['name']} — {ns.get('reason', 'suppressed')}")
        lines.append("")

    if spec["authority_order"]:
        lines.append("ACTIVE AUTHORITY CHAIN (highest to lowest):")
        current_type = None
        for b in spec["authority_order"]:
            if b["type"] != current_type:
                current_type = b["type"]
                rank = b["authority_rank"]
                lines.append(f"  [{rank}] {b['type']}")
            lines.append(f"       → {b['name']}  ({b['neoblock']})")
        lines.append("")

    if spec["suppressed_blocks_detail"]:
        lines.append(f"SUPPRESSED BLOCKS ({len(spec['suppressed_blocks_detail'])}):")
        for b in spec["suppressed_blocks_detail"][:8]:
            lines.append(f"  ✗ [{b['type']}] {b['name']} — {b['reason']}")
        if len(spec["suppressed_blocks_detail"]) > 8:
            lines.append(f"  ... and {len(spec['suppressed_blocks_detail'])-8} more")
        lines.append("")

    if spec["dominant_directive"]:
        lines.append(f"DOMINANT DIRECTIVE: {spec['dominant_directive']}")
    lines.append(f"COGNITIVE SUMMARY: {mm.get('cognitive_summary', '')}")

    if spec["warnings"]:
        lines.append("")
        lines.append("WARNINGS:")
        for w in spec["warnings"]:
            lines.append(f"  ⚠ {w}")

    return {
        "sleeve_name": spec["sleeve_name"],
        "runtime_id": spec["runtime_id"],
        "explanation": "\n".join(lines),
        "active_stacks": len(spec["active_neostacks"]),
        "suppressed_stacks": len(spec["suppressed_neostacks"]),
        "active_blocks": spec["active_blocks_count"],
        "suppressed_blocks": spec["suppressed_blocks_count"],
        "dominant_directive": spec["dominant_directive"],
        "warnings": spec["warnings"]
    }


@mcp.tool()
def umg_preview_gate_eval(sleeve_json: str, active_context: list[str] = None) -> dict:
    """
    Preview Phase 2a gate evaluation and vertical hierarchy resolution.

    Input contract:
    - sleeve_json: serialized sleeve JSON with v0.2 gate expressions embedded in NeoStacks.gates[]
    - active_context: list of signal names, or omitted for fallback-only/default behavior

    Output contract:
    - runtime_id, sleeve_id, sleeve_name, source_mode, active_context
    - gate_evaluations[] with exact threshold score/threshold fields
    - active_stacks[] sorted by gate priority
    - active_blocks[] after vertical hierarchy dominance
    - suppressed_items[] with explicit reason codes
    - conflicts[] authority-conflict records
    - vertical_resolution summary
    - route_trace[] entries for gate_evaluation and vertical_resolution passes
    """
    try:
        sleeve = json.loads(sleeve_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}

    runtime_spec = _run_phase2a_preview(sleeve, active_context or [])
    return runtime_spec


@mcp.tool()
def search_blocks(query: str, block_type: str = None, limit: int = 20) -> dict:
    query_lower = query.lower()
    limit = min(limit, 100)

    if block_type:
        btype_upper = block_type.upper()
        if btype_upper not in LIBRARY:
            return {
                "error": f"Unknown block type '{block_type}'.",
                "valid_types": list(LIBRARY.keys()),
                "results": []
            }
        pool = LIBRARY[btype_upper]
    else:
        pool = ALL_BLOCKS

    results = []
    for block in pool:
        name_lower = block["name"].lower()
        if query_lower in name_lower:
            score = 3 if name_lower.startswith(query_lower) else 2 if re.search(r'\b' + re.escape(query_lower), name_lower) else 1
            results.append({
                **block,
                "authority_rank": AUTHORITY_RANK.get(block["type"], 99),
                "type_description": TYPE_DESCRIPTIONS.get(block["type"], ""),
                "_score": score
            })

    results.sort(key=lambda x: (x.get("authority_rank", 99), -x["_score"], x["name"]))
    clean = [{k: v for k, v in r.items() if k != "_score"} for r in results[:limit]]

    return {
        "query": query,
        "block_type_filter": block_type or "ALL",
        "total_matches": len(results),
        "showing": len(clean),
        "results": clean
    }


@mcp.tool()
def audit_sleeve(sleeve_json: str) -> dict:
    try:
        sleeve = json.loads(sleeve_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}", "passed": False}

    issues = []
    canonical_count = 0
    custom_count = 0
    type_counts = {}

    for ns in sleeve.get("neoStacks", []):
        for gate in ns.get("gates", []):
            if gate.get("type") == "TRIGGER":
                if gate.get("name") not in NAME_IDX.get("TRIGGER", {}):
                    issues.append(f"Unknown TRIGGER gate: '{gate.get('name')}'")
                    custom_count += 1
                else:
                    canonical_count += 1
            elif gate.get("operator") not in {"any", "all", "not", "threshold", "priority", "fallback"}:
                issues.append(f"Unknown v0.2 gate operator: '{gate.get('operator')}'")

        for nb in ns.get("neoBlocks", []):
            nb_types = set()
            blocks = nb.get("blocks", [])
            ranks = [AUTHORITY_RANK.get(b.get("type", ""), 99) for b in blocks]
            if ranks != sorted(ranks):
                issues.append(
                    f"NeoBlock '{nb.get('name')}' blocks are not in authority order (DIRECTIVE first). Current order: "
                    f"{' → '.join(b.get('type','?') for b in blocks)}"
                )

            for block in blocks:
                btype = block.get("type", "")
                bname = block.get("name", "")
                if btype == "TRIGGER":
                    issues.append(f"TRIGGER '{bname}' inside NeoBlock '{nb.get('name')}' — TRIGGERs belong in gates only")
                elif bname in NAME_IDX.get(btype, {}):
                    canonical_count += 1
                else:
                    issues.append(f"Non-canonical [{btype}]: '{bname}' in '{nb.get('name')}'")
                    custom_count += 1

                nb_types.add(btype)
                type_counts[btype] = type_counts.get(btype, 0) + 1

            if len(nb_types) < 2:
                issues.append(f"NeoBlock '{nb.get('name')}' has only 1 block type — mix ≥2 types for cognitive coverage")

    total = canonical_count + custom_count
    coverage = round(canonical_count / total, 2) if total > 0 else 0

    return {
        "sleeve_name": sleeve.get("name") or sleeve.get("sleeve_name", "unnamed"),
        "passed": len(issues) == 0,
        "coverage_score": coverage,
        "canonical_blocks": canonical_count,
        "non_canonical_blocks": custom_count,
        "total_blocks_audited": total,
        "neostacks": len(sleeve.get("neoStacks", [])),
        "neoblocks": sum(len(ns.get("neoBlocks", [])) for ns in sleeve.get("neoStacks", [])),
        "type_distribution": type_counts,
        "issues": issues,
        "governance": {
            "sovereign_review_required": custom_count > 0 or len(issues) > 0,
            "runtime_eligible": len(issues) == 0 and coverage >= 0.9,
            "source_mode": sleeve.get("provenance", {}).get("sourceMode", "unknown"),
            "provenance_note": (
                "Clean native - all blocks canonical, authority order correct"
                if len(issues) == 0 and custom_count == 0
                else f"{custom_count} non-canonical block(s), {len(issues)} issue(s) - review required"
            )
        }
    }


@mcp.tool()
def get_block_types() -> dict:
    return {
        "framework": "Universal Modular Generation (UMG)",
        "total_blocks": TOTAL,
        "version": "0.2.0-preview",
        "sovereign": "NeoMAG",
        "license": "Apache-2.0",
        "authority_hierarchy_note": (
            "DIRECTIVE (rank 1) governs all blocks below it. "
            "PERSONA (rank 7) is a relational modifier. "
            "TRIGGER (rank 0) is a gate - never a body block."
        ),
        "types": {
            btype: {
                "prefix": LIBRARY[btype][0]["id"].split("-")[0],
                "authority_rank": AUTHORITY_RANK.get(btype, 99),
                "count": len(LIBRARY[btype]),
                "description": TYPE_DESCRIPTIONS[btype],
                "sample_blocks": [b["name"] for b in LIBRARY[btype][:5]],
                "role": (
                    "Gate only - activates NeoStack, never inside NeoBlock"
                    if btype == "TRIGGER"
                    else f"Body block - authority rank {AUTHORITY_RANK[btype]}"
                )
            }
            for btype in LIBRARY
        }
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
