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
  umg_build_neostack  — build a candidate NeoStack from purpose

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


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE_DIR, "blocks.json"), encoding="utf-8") as f:
    LIBRARY = json.load(f)

NAME_IDX = {
    t: {b["name"]: b for b in blocks}
    for t, blocks in LIBRARY.items()
}
ALL_BLOCKS = [b for blocks in LIBRARY.values() for b in blocks]
TOTAL = sum(len(v) for v in LIBRARY.values())

MOLT_AUTHORITY_RANKS = {
    "Directive": 1,
    "Instruction": 2,
    "Subject": 3,
    "Primary": 4,
    "Aim": 4,
    "Use": 4,
    "Need": 4,
    "Philosophy": 6,
    "Blueprint": 7,
    "Persona": 8,
}
AUTHORITY_RANK = {key.upper(): value for key, value in MOLT_AUTHORITY_RANKS.items()}

TYPE_DESCRIPTIONS = {
    "TRIGGER": "Gates - activation conditions that open a cognitive path. Never used inside NeoBlocks.",
    "DIRECTIVE": "Authority - strategic behavioral overlay and scope. Governs lower-rank content only on explicit contradiction.",
    "INSTRUCTION": "Method - procedural logic and execution approach.",
    "SUBJECT": "Target - domains, data entities, and objects of cognition.",
    "PRIMARY": "Outcome - core values and results being driven.",
    "PHILOSOPHY": "Worldview - ethical lens and decision framework.",
    "BLUEPRINT": "Structure - output format, schema, and form.",
    "PERSONA": "Voice - communication style and relational mode.",
    "AIM": "Meta-MOLT - primary-adjacent intent anchor used in composed/runtime-adjacent structures.",
    "USE": "Meta-MOLT - primary-adjacent use framing for composed/runtime-adjacent structures.",
    "NEED": "Meta-MOLT - primary-adjacent need framing for composed/runtime-adjacent structures.",
}

PURPOSE_BLOCK_MAP = {
    "debug": {
        "directives": ["Assess Accurately", "Identify Root Causes"],
        "instructions": ["Trace Causality", "Break Into Components", "Measure Against Baseline"],
        "subjects": ["Code", "System Architecture", "Metrics"],
        "primaries": ["Technical Precision", "Factual Accuracy"],
        "philosophies": ["First Principles Thinking"],
        "personas": ["Methodical"],
    },
    "research": {
        "directives": ["Assess Accurately", "Seek Truth"],
        "instructions": ["Compare Side By Side", "Identify Patterns"],
        "subjects": ["Knowledge Base", "Raw Data"],
        "primaries": ["Factual Accuracy", "Logical Correctness"],
        "philosophies": ["Empiricism"],
        "personas": ["Analytical"],
    },
    "plan": {
        "directives": ["Think Long Term", "Build Robustly"],
        "instructions": ["Define Milestones", "Sequence Tasks"],
        "subjects": ["Strategic Goals", "Stakeholders"],
        "primaries": ["Strategic Alignment", "Robustness"],
        "philosophies": ["Pragmatism"],
        "personas": ["Deliberate"],
    },
    "govern": {
        "directives": ["Honor Governance", "Be Transparent"],
        "instructions": ["Verify Tool Anchor", "Check Against Requirements"],
        "subjects": ["Governance Frameworks", "Governance Constraints"],
        "primaries": ["Human Sovereignty", "Governance Compliance"],
        "philosophies": ["Deontology"],
        "personas": ["Analytical"],
    },
    "create": {
        "directives": ["Generate Novelty", "Reveal Patterns"],
        "instructions": ["Identify Patterns", "Express Authentically"],
        "subjects": ["Frameworks", "Knowledge Base"],
        "primaries": ["Original Thinking", "Novelty"],
        "philosophies": ["Pragmatism"],
        "personas": ["Enthusiastic"],
    },
    "audit": {
        "directives": ["Assess Accurately", "Evaluate Objectively"],
        "instructions": ["Check Against Requirements", "Identify Weaknesses", "Measure Against Baseline"],
        "subjects": ["Governance Frameworks", "Metrics"],
        "primaries": ["Factual Accuracy", "Logical Correctness"],
        "philosophies": ["Stoicism"],
        "personas": ["Analytical"],
    },
}

COMPILATION_RULES = """
UMG COMPILATION RULES (follow exactly):

STRUCTURE:
- Sleeve: 1-3 NeoStacks
- NeoStack: 1-3 NeoBlocks + optional TRIGGER gates (0-2)
- NeoBlock: 2-5 blocks from non-TRIGGER types only
- TRIGGER blocks go in NeoStack gates[] ONLY - never inside NeoBlocks
- Each NeoBlock should mix at least 2 different block types
- Every compiled NeoBlock must contain at least one Directive

AUTHORITY ORDER within NeoBlocks (apply top-down):
  DIRECTIVE (1) → INSTRUCTION (2) → SUBJECT (3) → PRIMARY (4)
  → PHILOSOPHY (6) → BLUEPRINT (7) → PERSONA (8)

CANON:
- Merge is action / synthesis metadata, never a block type
- Off is runtime state / suppression metadata, never a body MOLT type
- Trigger is a gate, not a body block in the authority chain

OUTPUT FORMAT (governed sleeve JSON):
{
  "sleeve_name": "...",
  "neoStacks": [
    {
      "name": "...",
      "gates": [],
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
        "sleeve_id": sleeve.get("id", sleeve.get("sleeve_id", sleeve.get("sleeve_name", "unknown"))),
        "sleeve_name": sleeve.get("name", sleeve.get("sleeve_name", "unnamed")),
        "source_mode": sleeve.get("provenance", {}).get("sourceMode", "unknown"),
        "active_context": {
            "signals": sorted(_active_signal_set(active_context)),
            "raw": deepcopy(active_context) if active_context is not None else [],
        },
        "session_id": None,
        "turn_index": 1,
        "previous_runtime_id": None,
        "stateful_features_enabled": False,
        "gate_evaluations": [],
        "active_neostacks": [],
        "suppressed_items": [],
        "active_blocks": [],
        "conflicts": [],
        "warnings": [],
        "route_trace": [],
    }


def _stack_id(ns: dict, idx: int) -> str:
    return ns.get("id") or f"NS-{idx + 1}"


def _neoblock_id(nb: dict, ns_id: str, idx: int) -> str:
    return nb.get("id") or f"{ns_id}:NB-{idx + 1}"


def _block_id(block: dict, ns_id: str, nb_id: str, idx: int) -> str:
    return block.get("id") or f"{ns_id}:{nb_id}:BLK-{idx + 1}"


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


def _normalize_molt_type(value: str | None) -> str:
    return str(value or "").strip().title()


def _block_runtime_type(block: dict) -> str:
    return _normalize_molt_type(block.get("molt_type") or block.get("type"))


def _is_off_block(block: dict) -> bool:
    return _block_runtime_type(block) == "Off" or str(block.get("state", "")).strip().lower() == "off"


def _hierarchy_rank(block: dict):
    return MOLT_AUTHORITY_RANKS.get(_block_runtime_type(block))


def _block_dedupe_key(block: dict) -> str:
    return block.get("block_id") or block.get("id") or block.get("name")


def _build_trace_event(trace_id: str, event_type: str, reason_summary: str, *, object_id: str | None = None,
                       stage: str = "assembly", object_refs: list | None = None, molt_type: str | None = None) -> dict:
    event = {
        "trace_id": trace_id,
        "event_type": event_type,
        "stage": stage,
        "reason_summary": reason_summary,
    }
    if object_id is not None:
        event["object_id"] = object_id
    if object_refs is not None:
        event["object_refs"] = object_refs
    if molt_type is not None:
        event["molt_type"] = molt_type
    return event


def _assembly_row(row_id: str, layer: str, object_id: str, object_name: str, object_type: str, scope: str,
                  state: str, order_index: int, parent_id: str | None, route_id: str | None, gate_id: str | None,
                  trace_id: str, reason_summary: str, *, hydration_status: str = "not_required") -> dict:
    return {
        "row_id": row_id,
        "layer": layer,
        "object_id": object_id,
        "object_name": object_name,
        "object_type": object_type,
        "scope": scope,
        "state": state,
        "resolution_state": "unresolved",
        "gate_eval_state": "pending_eval",
        "order_index": order_index,
        "parent_id": parent_id,
        "route_id": None if route_id is None else route_id,
        "gate_id": gate_id,
        "tool_id": None,
        "trace_id": trace_id,
        "reason_summary": reason_summary,
        "risk_level": "none",
        "approval_required": False,
        "approval_status": "not_required",
        "hydration_status": hydration_status,
    }


def _build_selection_result(selection_id: str, selected_ids: list[str], candidate_ids: list[str], trace_ref: str) -> dict:
    return {
        "selection_id": selection_id,
        "selection_stage": "assembly",
        "selected_block_ids": selected_ids,
        "candidate_block_ids": candidate_ids,
        "suppressed_block_ids": [],
        "selection_reasons": [],
        "requires_hydration": False,
        "resolved": False,
        "trace_ref": trace_ref,
    }


def _build_runtime_spec_fragment(source_tool: str, candidate_sleeve_ref: str, stack_refs: list[str],
                                 block_refs: list[str], trace_refs: list[str]) -> dict:
    return {
        "resolved": False,
        "resolution_stage": "assembly",
        "requires_resolver": True,
        "source_tool": source_tool,
        "candidate_sleeve_ref": candidate_sleeve_ref,
        "candidate_route_refs": [],
        "candidate_stack_refs": stack_refs,
        "candidate_block_refs": block_refs,
        "trace_refs": trace_refs,
    }


def _build_assembly_source() -> dict:
    return {
        "mode": "canonical_library_direct",
        "future_mode": "block_card_retrieval_then_hydration",
        "package_index_used": False,
        "block_card_index_used": False,
        "hydration_performed": False,
    }


def _find_block_by_name(name: str, allowed_types: list[str] | None = None):
    allowed = {t.upper() for t in allowed_types} if allowed_types else None
    for block in ALL_BLOCKS:
        if block.get("name") != name:
            continue
        if allowed and block.get("type", "").upper() not in allowed:
            continue
        cloned = deepcopy(block)
        cloned["molt_type"] = _normalize_molt_type(cloned.get("type"))
        return cloned
    return None


def _select_first_available(names: list[str], allowed_types: list[str] | None = None):
    for name in names:
        block = _find_block_by_name(name, allowed_types)
        if block:
            return block
    return None


def _safe_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug or "candidate"


def _build_gate_from_signals(gate_id: str, description: str, signals: list[str], priority: int = 70) -> dict:
    return {
        "gate_id": gate_id,
        "operator": "any",
        "conditions": [{"signal": signal} for signal in signals],
        "priority": priority,
        "description": description,
    }


def _coerce_gate_signals(gate_signals: str | None, purpose: str):
    warnings = []
    if not gate_signals:
        purpose_l = purpose.lower()
        if any(word in purpose_l for word in ["debug", "bug", "trace", "root cause", "code"]):
            return ["debugging_request"], warnings
        if any(word in purpose_l for word in ["research", "investigate", "verify"]):
            return ["research_request"], warnings
        if any(word in purpose_l for word in ["govern", "policy", "review"]):
            return ["governance_review"], warnings
        if any(word in purpose_l for word in ["plan", "roadmap", "sequence"]):
            return ["planning_request"], warnings
        if any(word in purpose_l for word in ["create", "brainstorm", "novel"]):
            return ["creative_request"], warnings
        return [], warnings
    try:
        parsed = json.loads(gate_signals)
        if isinstance(parsed, list):
            return [str(x) for x in parsed if str(x).strip()], warnings
    except Exception:
        warnings.append("gate_signals_parse_failed")
    inferred, _ = _coerce_gate_signals(None, purpose)
    return inferred, warnings


def _explicitly_contradicts(high_name: str, low_name: str) -> bool:
    hi = high_name.lower()
    lo = low_name.lower()
    contradiction_pairs = [
        (("honor governance",), ("bypass governance constraints", "override governance", "ignore governance")),
        (("be transparent",), ("conceal reasoning", "hide rationale", "opaque output")),
        (("assess accurately",), ("invent facts", "fabricate", "speculate without basis")),
    ]
    for high_terms, low_terms in contradiction_pairs:
        if any(term in hi for term in high_terms) and any(term in lo for term in low_terms):
            return True
    return False


def _flatten_results(results_by_query: dict) -> list:
    flat = []
    seen = set()
    for matches in results_by_query.values():
        for block in matches:
            key = _block_dedupe_key(block)
            if key in seen:
                continue
            seen.add(key)
            flat.append(block)
    return flat


def evaluate_gates(runtime_spec: dict, sleeve: dict, active_context) -> dict:
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
            negated_conditions = [_normalize_signal_name(s) for s in gate.get("negated_conditions", []) if _normalize_signal_name(s)]
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
                        "No condition matched." if not matched_conditions else
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
                    score = round(sum(float(c.get("gate_weight", 1.0)) for c in conditions if _normalize_signal_name(c.get("signal")) in signals), 6)
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
            runtime_spec["active_neostacks"].append({
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
            runtime_spec["active_neostacks"].append({
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


def resolve_vertical_hierarchy(runtime_spec: dict, sleeve: dict) -> dict:
    step_index = len(runtime_spec["route_trace"])
    active_stack_ids = {s["stack_id"] for s in runtime_spec.get("active_neostacks", [])}
    active_by_rank = {
        "Directive": [],
        "Instruction": [],
        "Subject": [],
        "Primary": [],
        "Philosophy": [],
        "Blueprint": [],
        "Persona": [],
    }
    cross_rank_conflicts = []
    same_rank_tensions = []
    escalated_conflicts = []
    off_suppressed = []
    warnings = []
    active_blocks = []

    candidate_blocks = []
    for ns_idx, ns in enumerate(sleeve.get("neoStacks", [])):
        stack_id = _stack_id(ns, ns_idx)
        if stack_id not in active_stack_ids:
            continue
        stack_priority = next((s["priority"] for s in runtime_spec["active_neostacks"] if s["stack_id"] == stack_id), 0)
        for nb_idx, nb in enumerate(ns.get("neoBlocks", [])):
            nb_id = _neoblock_id(nb, stack_id, nb_idx)
            for blk_idx, block in enumerate(nb.get("blocks", [])):
                block_copy = deepcopy(block)
                runtime_type = _block_runtime_type(block_copy)
                block_copy["type"] = runtime_type.upper() if runtime_type else block_copy.get("type", "")
                block_copy["molt_type"] = runtime_type
                candidate_blocks.append({
                    "block_id": _block_id(block_copy, stack_id, nb_id, blk_idx),
                    "block_name": block_copy.get("name", ""),
                    "molt_type": runtime_type,
                    "authority_rank": _hierarchy_rank(block_copy),
                    "neoblock_id": nb_id,
                    "neostack_id": stack_id,
                    "source": "library" if block_copy.get("name") in NAME_IDX.get(block_copy.get("type", ""), {}) else "candidate",
                    "stack_priority": stack_priority,
                    "state": str(block_copy.get("state", "")).strip().lower(),
                })

    blocked_ids = set()

    for block in candidate_blocks:
        if _is_off_block(block):
            target_name = block["block_name"]
            for other in candidate_blocks:
                if other["block_id"] == block["block_id"]:
                    continue
                if other["block_name"] == target_name:
                    blocked_ids.add(other["block_id"])
                    entry = {
                        "id": other["block_id"],
                        "suppression_reason": "off_block",
                        "suppressed_by_id": block["block_id"],
                        "reason": f"Suppressed by Off state for {target_name}.",
                    }
                    runtime_spec["suppressed_items"].append(entry)
                    off_suppressed.append(entry)

    typed_blocks = []
    for block in candidate_blocks:
        if block["block_id"] in blocked_ids or _is_off_block(block):
            continue
        if block["authority_rank"] is None:
            warnings.append({
                "warning_type": "unknown_molt_type",
                "block_ids": [block["block_id"]],
                "reason": f"Unknown MOLT type '{block['molt_type']}' skipped for hierarchy.",
            })
            continue
        typed_blocks.append(block)
        active_by_rank[block["molt_type"]].append(block["block_name"])
        active_blocks.append({k: block[k] for k in ["block_id", "block_name", "molt_type", "authority_rank", "neoblock_id", "neostack_id", "source"]})

    rank_buckets = {}
    for block in typed_blocks:
        rank_buckets.setdefault(block["authority_rank"], []).append(block)

    for rank, blocks in rank_buckets.items():
        for i, left in enumerate(blocks):
            for right in blocks[i + 1:]:
                if left["neostack_id"] != right["neostack_id"] or left["block_name"] == right["block_name"]:
                    continue
                same_rank_tensions.append({
                    "rank": rank,
                    "blocks": [left["block_name"], right["block_name"]],
                    "reason": "possible_tension",
                })

    for higher_rank in sorted(rank_buckets.keys()):
        for lower_rank in sorted(r for r in rank_buckets.keys() if r > higher_rank):
            for high in rank_buckets[higher_rank]:
                for low in rank_buckets[lower_rank]:
                    if low["block_id"] in blocked_ids:
                        continue
                    if _explicitly_contradicts(high["block_name"], low["block_name"]):
                        blocked_ids.add(low["block_id"])
                        reason = f"Explicit contradiction: {high['block_name']} governs {low['block_name']}."
                        runtime_spec["suppressed_items"].append({
                            "id": low["block_id"],
                            "suppression_reason": "higher_vertical_authority",
                            "suppressed_by_id": high["block_id"],
                            "reason": reason,
                        })
                        cross_rank_conflicts.append({
                            "winner_block": high["block_name"],
                            "loser_block": low["block_name"],
                            "winner_id": high["block_id"],
                            "loser_id": low["block_id"],
                            "reason": reason,
                        })
                    elif high["block_name"] != low["block_name"] and high["neostack_id"] != low["neostack_id"]:
                        warnings.append({
                            "warning_type": "possible_tension",
                            "block_ids": [high["block_id"], low["block_id"]],
                            "reason": f"Possible tension between {high['block_name']} and {low['block_name']}.",
                        })

    runtime_spec["active_blocks"] = [b for b in active_blocks if b["block_id"] not in blocked_ids]
    runtime_spec["warnings"].extend(warnings)
    runtime_spec["vertical_resolution"] = {
        "active_by_rank": active_by_rank,
        "cross_rank_conflicts": cross_rank_conflicts,
        "same_rank_tensions": same_rank_tensions,
        "escalated_conflicts": escalated_conflicts,
        "off_suppressed": off_suppressed,
    }
    runtime_spec["conflicts"].extend([
        {
            "conflict_id": f"CONF-{item['winner_id']}-{item['loser_id']}",
            "involved_ids": [item["winner_id"], item["loser_id"]],
            "conflict_type": "authority_conflict",
            "resolution_status": "suppressed_lower",
            "winner_id": item["winner_id"],
            "reason": item["reason"],
        }
        for item in cross_rank_conflicts
    ])

    for block in runtime_spec["active_blocks"]:
        runtime_spec["route_trace"].append(_make_trace_entry(
            "vertical_resolution",
            step_index,
            block["block_id"],
            "active",
            f"{block['molt_type']} block active as horizontal peer or uncontested block.",
            {
                "molt_type": block["molt_type"],
                "authority_rank": block["authority_rank"],
                "neostack_id": block["neostack_id"],
            },
        ))
        step_index += 1

    for conflict in cross_rank_conflicts:
        runtime_spec["route_trace"].append(_make_trace_entry(
            "vertical_resolution",
            step_index,
            conflict["loser_id"],
            "suppressed",
            conflict["reason"],
            {
                "winner_id": conflict["winner_id"],
                "loser_id": conflict["loser_id"],
                "resolution_rule": "higher_vertical_authority",
            },
        ))
        step_index += 1

    return runtime_spec


def _generate_warnings(active_blocks: list, suppressed_blocks: list) -> list:
    warnings = []
    active_types = {b.get("type") or b.get("molt_type") for b in active_blocks}
    if "DIRECTIVE" not in active_types and "Directive" not in active_types and active_blocks:
        warnings.append("No active DIRECTIVE block — cognitive authority anchor missing")
    if "INSTRUCTION" not in active_types and "Instruction" not in active_types and active_blocks:
        warnings.append("No active INSTRUCTION block — execution method undefined")
    if "PRIMARY" not in active_types and "Primary" not in active_types and active_blocks:
        warnings.append("No active PRIMARY block — outcome anchor missing")
    if len(active_blocks) == 0:
        warnings.append("No active blocks — all NeoStacks suppressed. Check active_context triggers.")
    if suppressed_blocks and not active_blocks:
        warnings.append(f"{len(suppressed_blocks)} block(s) suppressed with nothing active — no trigger matched any NeoStack gate")
    return warnings


def _build_molt_map(active_blocks: list, suppressed_blocks: list, trigger_evaluations: list, vertical_resolution: dict | None = None) -> dict:
    rank_map = vertical_resolution.get("active_by_rank", {}) if vertical_resolution else {}
    authority_chain = {}
    for btype in ["Directive", "Instruction", "Subject", "Primary", "Philosophy", "Blueprint", "Persona"]:
        authority_chain[btype] = rank_map.get(btype, []) or [
            b.get("block_name") or b.get("name")
            for b in active_blocks
            if (b.get("molt_type") or _normalize_molt_type(b.get("type"))) == btype
        ]

    return {
        "Directive": authority_chain["Directive"],
        "Instruction": authority_chain["Instruction"],
        "Subject": authority_chain["Subject"],
        "Primary": authority_chain["Primary"],
        "Philosophy": authority_chain["Philosophy"],
        "Blueprint": authority_chain["Blueprint"],
        "Persona": authority_chain["Persona"],
        "Suppressed": [b.get("block_name") or b.get("name") for b in suppressed_blocks],
        "Off": [item.get("id") for item in (vertical_resolution or {}).get("off_suppressed", [])],
        "Conflicts": [c.get("reason") for c in (vertical_resolution or {}).get("cross_rank_conflicts", [])],
        "cognitive_summary": (
            f"Directives: {len(authority_chain['Directive'])} active · "
            f"Instructions: {len(authority_chain['Instruction'])} active · "
            f"Primary: {len(authority_chain['Primary'])} active · "
            f"Philosophy: {len(authority_chain['Philosophy'])} active · "
            f"Persona: {len(authority_chain['Persona'])} active"
        )
    }


def _build_ir_graph(sleeve: dict, active_neostacks: list, suppressed_neostacks: list) -> dict:
    nodes = []
    edges = []
    active_route = []
    suppressed_routes = []

    sleeve_id = sleeve.get("id", sleeve.get("sleeve_id", "SL-unknown"))
    sleeve_name = sleeve.get("name", sleeve.get("sleeve_name", "unnamed"))
    nodes.append({"id": sleeve_id, "type": "sleeve", "label": sleeve_name, "state": "active", "authority_rank": None, "source_ref": sleeve_id})
    active_route.append(sleeve_id)

    for ns in active_neostacks:
        ns_id = ns.get("id", f"NS-{ns['name']}")
        nodes.append({"id": ns_id, "type": "neostack", "label": ns["name"], "state": "active", "authority_rank": None, "source_ref": ns_id})
        edges.append({"from": sleeve_id, "to": ns_id, "type": "contains", "state": "active", "reason": "sleeve contains this NeoStack"})
        active_route.append(ns_id)

        for gate in ns.get("gates", []):
            gate_id = gate.get("id", gate.get("gate_id", f"TRG-{gate.get('name', '').replace(' ', '-') }"))
            nodes.append({"id": gate_id, "type": "trigger_gate", "label": gate.get("name", gate_id), "state": "active", "authority_rank": 0, "source_ref": gate_id})
            edges.append({"from": gate_id, "to": ns_id, "type": "activates", "state": "active", "reason": "trigger gate matched - activates NeoStack"})

        for nb in ns.get("_neoblocks", ns.get("neoBlocks", [])):
            nb_id = nb.get("id", f"NB-{nb['name']}")
            nodes.append({"id": nb_id, "type": "neoblock", "label": nb["name"], "state": "active", "authority_rank": None, "source_ref": nb_id})
            edges.append({"from": ns_id, "to": nb_id, "type": "routes_to", "state": "active", "reason": "NeoStack routes to NeoBlock"})
            active_route.append(nb_id)
            blocks = nb.get("_blocks_by_authority", nb.get("blocks", []))
            for block in blocks:
                b_id = block.get("id", f"{block.get('type', 'B')}-{block.get('name', '').replace(' ', '-')}")
                nodes.append({
                    "id": b_id,
                    "type": "molt_block",
                    "label": f"[{block.get('type', '')}] {block.get('name', '')}",
                    "state": "active",
                    "authority_rank": AUTHORITY_RANK.get(block.get("type", ""), None),
                    "source_ref": b_id,
                })
                edges.append({"from": nb_id, "to": b_id, "type": "contains", "state": "active", "reason": "authority-ordered body block"})
                active_route.append(b_id)

    for ns in suppressed_neostacks:
        ns_id = ns.get("id", f"NS-{ns['name']}")
        suppressed_path = [ns_id]
        nodes.append({"id": ns_id, "type": "neostack", "label": ns["name"], "state": "suppressed", "authority_rank": None, "source_ref": ns_id})
        edges.append({"from": sleeve_id, "to": ns_id, "type": "contains", "state": "suppressed", "reason": "NeoStack suppressed - trigger gate not matched"})
        for gate in ns.get("gates", []):
            gate_id = gate.get("id", gate.get("gate_id", f"TRG-{gate.get('name', '').replace(' ', '-') }"))
            nodes.append({"id": gate_id, "type": "trigger_gate", "label": gate.get("name", gate_id), "state": "inactive", "authority_rank": 0, "source_ref": gate_id})
            edges.append({"from": gate_id, "to": ns_id, "type": "suppresses", "state": "inactive", "reason": "trigger gate not matched - NeoStack suppressed"})
            suppressed_path.append(gate_id)
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
        },
    }


def _build_runtime_spec(sleeve: dict, active_context: list) -> dict:
    active_context_safe = active_context if active_context else []
    runtime = _run_phase2a_preview(sleeve, active_context_safe)

    active_neostacks = []
    suppressed_neostacks = []
    active_ids = {s["stack_id"] for s in runtime.get("active_neostacks", [])}
    for idx, ns in enumerate(sleeve.get("neoStacks", [])):
        stack_id = _stack_id(ns, idx)
        ns_resolved = deepcopy(ns)
        if stack_id in active_ids:
            active_neostacks.append(ns_resolved)
        else:
            suppressed_neostacks.append(ns_resolved)

    active_blocks_full = []
    suppressed_blocks = []
    active_block_ids = {b["block_id"] for b in runtime.get("active_blocks", [])}
    for ns_idx, ns in enumerate(sleeve.get("neoStacks", [])):
        stack_id = _stack_id(ns, ns_idx)
        for nb_idx, nb in enumerate(ns.get("neoBlocks", [])):
            nb_id = _neoblock_id(nb, stack_id, nb_idx)
            for blk_idx, block in enumerate(nb.get("blocks", [])):
                bid = _block_id(block, stack_id, nb_id, blk_idx)
                wrapped = {
                    **deepcopy(block),
                    "_neoblock": nb.get("name", ""),
                    "_neostack": ns.get("name", ""),
                    "_authority_rank": AUTHORITY_RANK.get(block.get("type", ""), None),
                    "id": bid,
                }
                if bid in active_block_ids:
                    active_blocks_full.append(wrapped)
                else:
                    suppressed_blocks.append(wrapped)

    authority_order = sorted(
        runtime.get("active_blocks", []),
        key=lambda b: (b.get("authority_rank") if b.get("authority_rank") is not None else 999, b.get("block_name", ""))
    )
    dominant_directive = next((b for b in authority_order if b.get("molt_type") == "Directive"), None)
    warnings = _generate_warnings(active_blocks_full, suppressed_blocks)
    for item in runtime.get("warnings", []):
        if isinstance(item, dict):
            warnings.append(item.get("reason", "warning"))
        else:
            warnings.append(str(item))

    suppressed_details = []
    suppress_map = {item["id"]: item for item in runtime.get("suppressed_items", [])}
    for block in suppressed_blocks:
        meta = suppress_map.get(block["id"], {})
        suppressed_details.append({
            "id": block["id"],
            "type": block.get("type", ""),
            "name": block.get("name", ""),
            "neoblock": block.get("_neoblock", ""),
            "neostack": block.get("_neostack", ""),
            "reason": meta.get("reason", "suppressed by runtime resolution"),
        })

    runtime["trigger_evaluations"] = runtime.pop("gate_evaluations", [])
    runtime["molt_map"] = _build_molt_map(active_blocks_full, suppressed_blocks, runtime["trigger_evaluations"], runtime.get("vertical_resolution"))
    runtime["ir_graph"] = _build_ir_graph(sleeve, active_neostacks, suppressed_neostacks)
    runtime["route_purity"] = "clean_native" if not any(b.get("custom") for b in active_blocks_full) else "mixed"
    runtime["active_blocks_count"] = len(active_blocks_full)
    runtime["suppressed_blocks_count"] = len(suppressed_blocks)
    runtime["total_neostacks"] = len(sleeve.get("neoStacks", []))
    runtime["dominant_directive"] = dominant_directive.get("block_name") if dominant_directive else None
    runtime["authority_order"] = [
        {
            "id": b.get("block_id", ""),
            "type": b.get("molt_type", ""),
            "name": b.get("block_name", ""),
            "neoblock": b.get("neoblock_id", ""),
            "neostack": b.get("neostack_id", ""),
            "authority_rank": b.get("authority_rank"),
        }
        for b in authority_order
    ]
    runtime["suppressed_blocks_detail"] = suppressed_details
    runtime["warnings"] = warnings
    runtime["active_neostacks"] = [{"id": _stack_id(ns, idx), "name": ns.get("name", "")} for idx, ns in enumerate(active_neostacks)]
    runtime["suppressed_neostacks"] = [
        {
            "id": _stack_id(ns, idx),
            "name": ns.get("name", ""),
            "reason": next((item["reason"] for item in runtime.get("suppressed_items", []) if item["id"] == _stack_id(ns, idx)), "suppressed"),
        }
        for idx, ns in enumerate(suppressed_neostacks)
    ]
    return runtime


def _run_phase2a_preview(sleeve: dict, active_context) -> dict:
    runtime_spec = _make_runtime_seed(sleeve, active_context)
    runtime_spec = evaluate_gates(runtime_spec, sleeve, active_context)
    runtime_spec = resolve_vertical_hierarchy(runtime_spec, sleeve)
    return runtime_spec


def _purpose_key(purpose: str) -> str:
    lower = purpose.lower()
    if any(word in lower for word in ["debug", "bug", "trace", "root cause", "code"]):
        return "debug"
    if any(word in lower for word in ["research", "verify", "investigate"]):
        return "research"
    if any(word in lower for word in ["plan", "roadmap", "sequence"]):
        return "plan"
    if any(word in lower for word in ["govern", "policy", "review"]):
        return "govern"
    if any(word in lower for word in ["create", "novel", "brainstorm"]):
        return "create"
    if any(word in lower for word in ["audit", "check", "validate"]):
        return "audit"
    return "govern"


def _assemble_neoblock_from_map(block_map: dict, block_count: int, warnings: list[str], neoblock_name: str):
    chosen = []
    selected_meta = []

    directive = _select_first_available(block_map.get("directives", []), ["DIRECTIVE"])
    if not directive:
        directive = _select_first_available(["Honor Governance", "Assess Accurately"], ["DIRECTIVE"])
        warnings.append("directive_fallback_used")
    if directive:
        chosen.append(directive)
        selected_meta.append({"name": directive["name"], "type": directive["type"], "selection_reason": "directive anchor"})

    ordered_groups = [
        ("instructions", ["INSTRUCTION"]),
        ("subjects", ["SUBJECT"]),
        ("primaries", ["PRIMARY"]),
        ("philosophies", ["PHILOSOPHY"]),
        ("personas", ["PERSONA"]),
    ]
    for key, allowed in ordered_groups:
        for name in block_map.get(key, []):
            if len(chosen) >= block_count:
                break
            block = _find_block_by_name(name, allowed)
            if block and all(existing["name"] != block["name"] for existing in chosen):
                chosen.append(block)
                selected_meta.append({"name": block["name"], "type": block["type"], "selection_reason": f"selected from {key}"})
        if len(chosen) >= block_count:
            break

    chosen = chosen[:max(3, min(block_count, 8))]
    if directive and directive["name"] not in [b["name"] for b in chosen]:
        chosen.insert(0, directive)
        chosen = chosen[:max(3, min(block_count, 8))]

    chosen_sorted = sorted(chosen, key=lambda b: AUTHORITY_RANK.get(b.get("type", ""), 999))
    for block in chosen_sorted:
        if _normalize_molt_type(block.get("type")) in {"Merge", "Off"}:
            warnings.append(f"invalid_molt_type:{block.get('type')}")
        block["molt_type"] = _normalize_molt_type(block.get("type"))

    return {
        "name": neoblock_name,
        "blocks": [{"type": block["type"], "name": block["name"], "id": block.get("id"), "molt_type": block.get("molt_type")} for block in chosen_sorted],
    }, selected_meta


def _build_assembly_metadata(source_tool: str, sleeve_name: str, neostacks: list, trace_events: list):
    stack_refs = [stack.get("id") or stack.get("name") for stack in neostacks]
    block_refs = []
    rows = []
    order_index = 0
    sleeve_id = f"sleeve.{_safe_slug(sleeve_name)}.v1"
    route_id = None

    trace_id = "trace.assembly.sleeve.001"
    rows.append(_assembly_row("row.assembly.sleeve.001", "sleeve", sleeve_id, sleeve_name, "Sleeve", "assembly", "assembled", order_index, None, route_id, None, trace_id, "Candidate sleeve assembled from canonical library blocks."))
    order_index += 1

    for stack_i, stack in enumerate(neostacks, start=1):
        stack_id = stack.get("id") or f"stack.{_safe_slug(stack.get('name', f'stack_{stack_i}'))}.v1"
        stack["id"] = stack_id
        gate = stack.get("gates", [None])[0] if stack.get("gates") else None
        gate_id = gate.get("gate_id") if gate else None
        trace_id = f"trace.assembly.stack.{stack_i:03d}"
        rows.append(_assembly_row(f"row.assembly.stack.{stack_i:03d}", "stack", stack_id, stack.get("name", stack_id), "NeoStack", "assembly", "assembled", order_index, sleeve_id, route_id, gate_id, trace_id, f"Assembled as candidate stack {stack.get('name', stack_id)} from intent/purpose."))
        trace_events.append(_build_trace_event(trace_id, "stack_assembled", f"Assembled candidate stack {stack.get('name', stack_id)}.", object_id=stack_id))
        order_index += 1
        if gate_id:
            gate_trace = f"trace.gate.assign.{stack_i:03d}"
            rows.append(_assembly_row(f"row.assembly.gate.{stack_i:03d}", "gate", gate_id, gate_id, "Gate", "assembly", "pending_eval", order_index, stack_id, route_id, gate_id, gate_trace, "Gate assigned at assembly time and pending runtime evaluation."))
            trace_events.append(_build_trace_event(gate_trace, "gate_assigned", f"Assigned gate {gate_id} to candidate stack {stack.get('name', stack_id)}.", object_id=gate_id))
            order_index += 1
        for nb_i, nb in enumerate(stack.get("neoBlocks", []), start=1):
            nb_id = nb.get("id") or f"neoblock.{_safe_slug(nb.get('name', f'neoblock_{nb_i}'))}.v1"
            nb["id"] = nb_id
            for blk_i, block in enumerate(nb.get("blocks", []), start=1):
                block_id = block.get("id") or f"blk.{_safe_slug(block.get('name', f'block_{blk_i}'))}.v1"
                block["id"] = block_id
                block_refs.append(block_id)
                trace_id = f"trace.assembly.block.{len(block_refs):03d}"
                rows.append(_assembly_row(f"row.assembly.block.{len(block_refs):03d}", "block", block_id, block.get("name", block_id), block.get("type", "Block"), "assembly", "candidate", order_index, nb_id, route_id, gate_id, trace_id, f"Selected as candidate {block.get('type', 'block')} for assembled structure."))
                trace_events.append(_build_trace_event(trace_id, "block_selected", f"Selected {block.get('name', block_id)} as candidate block.", object_id=block_id, molt_type=_normalize_molt_type(block.get("type"))))
                order_index += 1

    selection_result = _build_selection_result(
        f"select.{source_tool}.{_safe_slug(sleeve_name)}.v1",
        block_refs,
        block_refs,
        "trace.selection.001",
    )
    runtime_spec_fragment = _build_runtime_spec_fragment(source_tool, sleeve_id, stack_refs, block_refs, [event["trace_id"] for event in trace_events])
    gate_summary = {
        "gates_created": sum(len(stack.get("gates", [])) for stack in neostacks),
        "gate_schema": "schemas/umg-gate-expr.schema.json",
        "gate_states": [
            {
                "gate_id": gate.get("gate_id"),
                "target_type": "stack",
                "target_id": stack.get("id"),
                "state": "pending_eval",
                "condition_summary": gate.get("description", "Candidate gate pending runtime evaluation."),
                "trace_ref": f"trace.gate.assign.{idx:03d}",
            }
            for idx, stack in enumerate(neostacks, start=1)
            for gate in stack.get("gates", [])
        ],
    }
    assembly_source = _build_assembly_source()
    return selection_result, runtime_spec_fragment, rows, trace_events, gate_summary, assembly_source


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
def compile_sleeve(intent: str, active_context: str = None) -> dict:
    intent_key = _purpose_key(intent)
    warnings = []
    selected_meta = []

    governance_core_map = {
        "directives": ["Honor Governance"],
        "instructions": ["Verify Tool Anchor"],
        "subjects": ["Governance Frameworks"],
        "primaries": ["Human Sovereignty"],
        "philosophies": ["Stoicism", "Deontology"],
        "personas": ["Analytical"],
    }
    primary_map = PURPOSE_BLOCK_MAP.get(intent_key, PURPOSE_BLOCK_MAP["govern"])
    if intent_key == "govern" and _purpose_key(intent) != "govern":
        warnings.append("intent_category_defaulted_to_governance")

    stack1_neoblock, meta1 = _assemble_neoblock_from_map(governance_core_map, 5, warnings, "Governance Core")
    selected_meta.extend(meta1)
    stack2_neoblock, meta2 = _assemble_neoblock_from_map(primary_map, 6, warnings, "Primary Capability")
    selected_meta.extend(meta2)

    slug = _safe_slug(intent)
    sleeve_name = f"{slug.upper()}.v1"
    neostacks = [
        {
            "id": f"stack.{slug}.governance_core.v1",
            "name": "Governance Core",
            "gates": [],
            "neoBlocks": [stack1_neoblock],
        },
        {
            "id": f"stack.{slug}.primary_capability.v1",
            "name": "Primary Capability",
            "gates": [_build_gate_from_signals(
                f"GATE_{slug.upper()}_PRIMARY",
                f"Activates on the most relevant signals for intent '{intent}'.",
                ["technical_request", "debugging_request"] if intent_key == "debug" else [f"{intent_key}_request"] if intent_key not in {"govern", "plan"} else ["governance_review"] if intent_key == "govern" else ["planning_request"],
                priority=80,
            )],
            "neoBlocks": [stack2_neoblock],
        },
    ]

    if any(word in intent.lower() for word in ["and", "plus", "with research", "with planning"]):
        optional_key = "research" if "research" in intent.lower() else "plan"
        optional_block, meta3 = _assemble_neoblock_from_map(PURPOSE_BLOCK_MAP[optional_key], 5, warnings, optional_key.title())
        selected_meta.extend(meta3)
        neostacks.append({
            "id": f"stack.{slug}.{optional_key}.v1",
            "name": optional_key.title(),
            "gates": [_build_gate_from_signals(f"GATE_{slug.upper()}_{optional_key.upper()}", f"Activates optional {optional_key} mode.", [f"{optional_key}_request"], priority=60)],
            "neoBlocks": [optional_block],
        })

    trace_events = [
        _build_trace_event("trace.assembly.intent.001", "intent_classified", f"Intent matched {intent_key} category for assembly.", object_refs=[]),
    ]
    selection_result, runtime_spec_fragment, ir_matrix_rows, trace_events, gate_summary, assembly_source = _build_assembly_metadata("compile_sleeve", sleeve_name, neostacks, trace_events)
    sleeve_json = {
        "sleeve_name": sleeve_name,
        "compiled_from_intent": intent,
        "neoStacks": neostacks,
    }

    return {
        "sleeve_name": sleeve_name,
        "compiled_from_intent": intent,
        "compilation_summary": {
            "stacks_created": len(neostacks),
            "blocks_selected": len(selection_result["selected_block_ids"]),
            "gates_assigned": gate_summary["gates_created"],
            "compilation_method": "intent_driven_assembly",
            "warnings": warnings,
        },
        "sleeve_json": sleeve_json,
        "selection_result": selection_result,
        "runtime_spec_fragment": runtime_spec_fragment,
        "ir_matrix_rows": ir_matrix_rows,
        "trace_events": trace_events,
        "gate_summary": gate_summary,
        "assembly_source": assembly_source,
        "usage_note": "Pass sleeve_json to umg_preview_gate_eval or inspect_active_state with your active context signals.",
        "sovereign_review_required": True,
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
        **spec["molt_map"],
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
        **spec["ir_graph"],
    }


@mcp.tool()
def explain_route(sleeve_json: str, active_context: list[str] = None) -> dict:
    try:
        sleeve = json.loads(sleeve_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}

    spec = _build_runtime_spec(sleeve, active_context or [])
    mm = spec["molt_map"]
    lines = [f"SLEEVE: {spec['sleeve_name']}", f"CONTEXT: {', '.join(spec['active_context']['signals']) or 'none provided'}", ""]
    if spec["active_neostacks"]:
        lines.append(f"ACTIVE NEOSTACKS ({len(spec['active_neostacks'])}):")
        for ns in spec["active_neostacks"]:
            ev = next((e for e in spec["trigger_evaluations"] if e["stack_name"] == ns["name"]), {})
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
        "warnings": spec["warnings"],
    }


@mcp.tool()
def umg_preview_gate_eval(sleeve_json: str, active_context: list[str] = None) -> dict:
    try:
        sleeve = json.loads(sleeve_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}
    return _run_phase2a_preview(sleeve, active_context or [])


@mcp.tool()
def search_blocks(query: str = None, block_type: str = None, limit: int = 20, queries: str = None, limit_per_query: int = 3) -> dict:
    if queries is not None:
        try:
            parsed = json.loads(queries)
            query_list = [str(item) for item in parsed if str(item).strip()]
        except Exception:
            return {"error": "Invalid queries JSON.", "mode": "batch", "results_by_query": {}, "flat_results": []}
        per_query = max(1, min(int(limit_per_query), 5))
        results_by_query = {}
        trace_events = []
        for idx, q in enumerate(query_list, start=1):
            single = search_blocks(query=q, block_type=block_type, limit=per_query)
            results_by_query[q] = single.get("results", [])
            trace_events.append(_build_trace_event(f"trace.search.{idx:03d}", "query_executed", f"Executed batch search query '{q}'.", object_refs=[_block_dedupe_key(b) for b in single.get("results", [])]))
        flat_results = _flatten_results(results_by_query)
        return {
            "mode": "batch",
            "query_count": len(query_list),
            "total_results": sum(len(v) for v in results_by_query.values()),
            "results_by_query": results_by_query,
            "flat_results": flat_results,
            "candidate_cards": [],
            "dedupe_key": "block_id",
            "trace_events": trace_events,
            "hydration_required": False,
        }

    if not query:
        return {"error": "query is required in single-query mode.", "results": []}

    query_lower = query.lower()
    limit = min(limit, 100)
    if block_type:
        btype_upper = block_type.upper()
        if btype_upper not in LIBRARY:
            return {"error": f"Unknown block type '{block_type}'.", "valid_types": list(LIBRARY.keys()), "results": []}
        pool = LIBRARY[btype_upper]
    else:
        pool = ALL_BLOCKS

    results = []
    for block in pool:
        name_lower = block["name"].lower()
        if query_lower in name_lower:
            score = 3 if name_lower.startswith(query_lower) else 2 if re.search(r"\b" + re.escape(query_lower), name_lower) else 1
            results.append({
                **deepcopy(block),
                "authority_rank": AUTHORITY_RANK.get(block["type"], 99),
                "type_description": TYPE_DESCRIPTIONS.get(block["type"], ""),
                "block_id": block.get("id"),
                "_score": score,
            })

    results.sort(key=lambda x: (x.get("authority_rank", 99), -x["_score"], x["name"]))
    clean = [{k: v for k, v in r.items() if k != "_score"} for r in results[:limit]]
    return {
        "query": query,
        "block_type_filter": block_type or "ALL",
        "total_matches": len(results),
        "showing": len(clean),
        "results": clean,
    }


@mcp.tool()
def umg_build_neostack(purpose: str, always_on: bool = False, gate_signals: str = None, block_count: int = 5) -> dict:
    key = _purpose_key(purpose)
    block_map = PURPOSE_BLOCK_MAP.get(key, PURPOSE_BLOCK_MAP["govern"])
    warnings = []
    count = max(3, min(int(block_count), 8))
    neoblock, selected_meta = _assemble_neoblock_from_map(block_map, count, warnings, f"{key.title()} Capability")
    signals, signal_warnings = _coerce_gate_signals(gate_signals, purpose)
    warnings.extend(signal_warnings)
    stack_name = f"{key.title()} Capability"
    stack_id = f"stack.{_safe_slug(purpose)}.v1"
    gates = [] if always_on else [_build_gate_from_signals(f"GATE_{_safe_slug(purpose).upper()}", f"Activates on {', '.join(signals) if signals else 'inferred signals'}.", signals or [f"{key}_request"], priority=70)]
    neostack_json = {"id": stack_id, "name": stack_name, "gates": gates, "neoBlocks": [neoblock]}
    trace_events = [_build_trace_event("trace.assembly.intent.001", "purpose_classified", f"Purpose matched {key} category for assembly.", object_refs=[])]
    selection_result, runtime_spec_fragment, ir_matrix_rows, trace_events, gate_summary, assembly_source = _build_assembly_metadata("umg_build_neostack", stack_name, [neostack_json], trace_events)
    return {
        "neostack_name": stack_name,
        "built_from_purpose": purpose,
        "neostack_json": neostack_json,
        "blocks_selected": selected_meta,
        "selection_result": selection_result,
        "runtime_spec_fragment": runtime_spec_fragment,
        "ir_matrix_rows": ir_matrix_rows,
        "trace_events": trace_events,
        "gate_assigned": gates[0] if gates else None,
        "assembly_source": assembly_source,
        "usage_note": "Drop this neostack_json into a sleeve neoStacks array.",
        "sovereign_review_required": True,
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
            ranks = [AUTHORITY_RANK.get(b.get("type", ""), 999) for b in blocks]
            if ranks != sorted(ranks):
                issues.append(f"NeoBlock '{nb.get('name')}' blocks are not in authority order. Current order: {' → '.join(b.get('type','?') for b in blocks)}")

            for block in blocks:
                btype = block.get("type", "")
                bname = block.get("name", "")
                if btype.upper() == "TRIGGER":
                    issues.append(f"TRIGGER '{bname}' inside NeoBlock '{nb.get('name')}' — TRIGGERs belong in gates only")
                elif btype.title() in {"Merge", "Off"}:
                    issues.append(f"Invalid body MOLT type '{btype}' in '{nb.get('name')}'")
                elif bname in NAME_IDX.get(btype.upper(), {}):
                    canonical_count += 1
                else:
                    issues.append(f"Non-canonical [{btype}]: '{bname}' in '{nb.get('name')}'")
                    custom_count += 1
                nb_types.add(btype)
                type_counts[btype] = type_counts.get(btype, 0) + 1

            if "DIRECTIVE" not in {t.upper() for t in nb_types}:
                issues.append(f"NeoBlock '{nb.get('name')}' is missing a Directive")
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
            "provenance_note": "Clean native - all blocks canonical, authority order correct" if len(issues) == 0 and custom_count == 0 else f"{custom_count} non-canonical block(s), {len(issues)} issue(s) - review required",
        },
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
            "DIRECTIVE (rank 1) governs lower-rank content only on explicit contradiction. "
            "PERSONA (rank 8) is a relational modifier. "
            "TRIGGER is a gate - never a body block. Merge and Off are not body MOLT types."
        ),
        "types": {
            btype: {
                "prefix": LIBRARY[btype][0]["id"].split("-")[0],
                "authority_rank": AUTHORITY_RANK.get(btype, None),
                "count": len(LIBRARY[btype]),
                "description": TYPE_DESCRIPTIONS.get(btype, ""),
                "sample_blocks": [b["name"] for b in LIBRARY[btype][:5]],
                "role": "Gate only - activates NeoStack, never inside NeoBlock" if btype == "TRIGGER" else f"Body block - authority rank {AUTHORITY_RANK.get(btype)}",
            }
            for btype in LIBRARY
        },
    }


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
