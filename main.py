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

Sovereign: NeoMAG  |  License: Apache 2.0  |  Version: 0.1.0
"""

import json
import os
import re
import time
from mcp.server.fastmcp import FastMCP

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
    "TRIGGER":     0,   # Gates only — never a body block
    "DIRECTIVE":   1,   # Highest authority — governs scope and behavior
    "INSTRUCTION": 2,   # Execution method
    "SUBJECT":     3,   # Target domain / object
    "PRIMARY":     4,   # Core outcome / value
    "PHILOSOPHY":  5,   # Ethical lens / worldview
    "BLUEPRINT":   6,   # Output structure / format
    "PERSONA":     7,   # Communication style (relational modifier)
}

TYPE_DESCRIPTIONS = {
    "TRIGGER":     "Gates — activation conditions that open a cognitive path. Never used inside NeoBlocks.",
    "DIRECTIVE":   "Authority — strategic behavioral overlay and scope. Governs all blocks below it.",
    "INSTRUCTION": "Method — procedural logic and execution approach.",
    "SUBJECT":     "Target — domains, data entities, and objects of cognition.",
    "PRIMARY":     "Outcome — core values and results being driven.",
    "PHILOSOPHY":  "Worldview — ethical lens and decision framework.",
    "BLUEPRINT":   "Structure — output format, schema, and form.",
    "PERSONA":     "Voice — communication style and relational mode.",
}

COMPILATION_RULES = """
UMG COMPILATION RULES (follow exactly):

STRUCTURE:
- Sleeve: 1-3 NeoStacks
- NeoStack: 1-3 NeoBlocks + optional TRIGGER gates (0-2)
- NeoBlock: 2-5 blocks from non-TRIGGER types only
- TRIGGER blocks go in NeoStack gates[] ONLY — never inside NeoBlocks
- Each NeoBlock should mix at least 2 different block types

AUTHORITY ORDER within NeoBlocks (apply top-down):
  DIRECTIVE (1) → INSTRUCTION (2) → SUBJECT (3) → PRIMARY (4)
  → PHILOSOPHY (5) → BLUEPRINT (6) → PERSONA (7)

NAMING: Use EXACT canonical block names from the library provided.
No fabrication — if a concept doesn't exist, flag it as custom.

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


# ── CORE RUNTIME ENGINE ───────────────────────────────────────────────────────
def _match_context(gate_name: str, active_context: list) -> bool:
    """Check if a trigger gate matches the active context."""
    gate_lower = gate_name.lower()
    for ctx in active_context:
        ctx_lower = ctx.lower()
        if gate_lower == ctx_lower:
            return True
        if gate_lower in ctx_lower or ctx_lower in gate_lower:
            return True
        # Word-level match
        gate_words = set(gate_lower.split())
        ctx_words = set(ctx_lower.split())
        if len(gate_words & ctx_words) >= 2:
            return True
    return False


def _generate_warnings(active_blocks: list, suppressed_blocks: list) -> list:
    """Generate runtime warnings about the active configuration."""
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
            f"{len(suppressed_blocks)} block(s) suppressed with nothing active — "
            "no trigger matched any NeoStack gate"
        )
    return warnings


def _build_molt_map(
    active_blocks: list,
    suppressed_blocks: list,
    trigger_evaluations: list
) -> dict:
    """Build the MOLT Map — cognitive envelope view of what the AI is doing."""

    active_trigger = next(
        (e["matched"][0] for e in trigger_evaluations
         if e.get("result") == "active" and e.get("matched")),
        "no trigger matched"
    )
    active_neostack = next(
        (e["neostack"] for e in trigger_evaluations
         if e.get("result") == "active"),
        "none"
    )

    # Group active blocks by type
    by_type = {}
    for btype in ["DIRECTIVE", "INSTRUCTION", "SUBJECT", "PRIMARY",
                  "PHILOSOPHY", "BLUEPRINT", "PERSONA"]:
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

    dominant_directive = (
        by_type["DIRECTIVE"][0]["name"]
        if by_type["DIRECTIVE"] else None
    )

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


def _build_ir_graph(
    sleeve: dict,
    active_neostacks: list,
    suppressed_neostacks: list
) -> dict:
    """Build the IR Graph — routing visibility showing how the system got here."""

    nodes = []
    edges = []
    active_route = []
    suppressed_routes = []

    sleeve_id = sleeve.get("id", sleeve.get("sleeve_id", "SL-unknown"))
    sleeve_name = sleeve.get("name", sleeve.get("sleeve_name", "unnamed"))

    # Sleeve node
    nodes.append({
        "id": sleeve_id,
        "type": "sleeve",
        "label": sleeve_name,
        "state": "active",
        "authority_rank": None,
        "source_ref": sleeve_id
    })
    active_route.append(sleeve_id)

    # Active NeoStacks
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

        # Trigger gates for this stack
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
                "reason": "trigger gate matched — activates NeoStack"
            })

        # NeoBlocks
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

            # Blocks sorted by authority
            blocks = nb.get("_blocks_by_authority", nb.get("blocks", []))
            blocks_sorted = sorted(
                blocks,
                key=lambda b: AUTHORITY_RANK.get(b.get("type", ""), 99)
            )
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

    # Suppressed NeoStacks
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
            "reason": "NeoStack suppressed — trigger gate not matched"
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
                "reason": "trigger gate not matched — NeoStack suppressed"
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
    """
    Core UMG runtime resolution engine.

    Resolves a sleeve against an active context to produce a RuntimeSpec —
    the single truth object from which all other views are derived.

    Suppression model (layered):
      1. Trigger gate mismatch → NeoStack suppressed
      2. Vertical hierarchy dominance → higher-ranked DIRECTIVE governs
      3. Parent suppression propagates down (stack → block → MOLT block)
    """
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
                "reason": "no gate — always active"
            }
        else:
            matched = [g.get("name", "") for g in gates
                       if _match_context(g.get("name", ""), active_context_safe)]
            unmatched = [g.get("name", "") for g in gates
                         if not _match_context(g.get("name", ""), active_context_safe)]

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

        # Resolve NeoBlocks (inherit parent state)
        resolved_neoblocks = []
        for nb in ns.get("neoBlocks", []):
            blocks_sorted = sorted(
                nb.get("blocks", []),
                key=lambda b: AUTHORITY_RANK.get(b.get("type", ""), 99)
            )
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

    # Flatten blocks
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
        reason = next(
            (e["reason"] for e in trigger_evaluations
             if e["neostack"] == ns.get("name", "")),
            "parent stack suppressed"
        )
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
    dominant_directive = next(
        (b for b in authority_order if b.get("type") == "DIRECTIVE"), None
    )

    molt_map = _build_molt_map(active_blocks, suppressed_blocks, trigger_evaluations)
    ir_graph = _build_ir_graph(sleeve, active_neostacks, suppressed_neostacks)
    warnings = _generate_warnings(active_blocks, suppressed_blocks)

    return {
        "runtime_id": f"RT-{int(time.time())}",
        "sleeve_id": sleeve.get("id", sleeve.get("sleeve_id", "unknown")),
        "sleeve_name": sleeve.get("name", sleeve.get("sleeve_name", "unnamed")),
        "source_mode": sleeve.get("provenance", {}).get("sourceMode", "unknown"),
        "route_purity": (
            "clean_native"
            if not any(b.get("custom") for b in active_blocks)
            else "mixed"
        ),
        "active_context": active_context_safe,
        "trigger_evaluations": trigger_evaluations,
        "active_neostacks": [
            {"id": ns.get("id", ""), "name": ns.get("name", "")}
            for ns in active_neostacks
        ],
        "suppressed_neostacks": [
            {
                "id": ns.get("id", ""),
                "name": ns.get("name", ""),
                "reason": next(
                    (e["reason"] for e in trigger_evaluations
                     if e["neostack"] == ns.get("name", "")), ""
                )
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
        "All compiled sleeves require sovereign (NeoMAG) review before ClawHub deployment."
    )
)


# ── TOOL: compile_sleeve ──────────────────────────────────────────────────────
@mcp.tool()
def compile_sleeve(intent: str, active_context: list[str] = None) -> dict:
    """
    Compile a governed UMG sleeve from plain language intent.

    Returns the canonical block library and compilation rules for Claude to
    assemble a governed sleeve JSON. If active_context is provided, also
    returns a preview of what would be active.

    Args:
        intent: Plain language description of what the sleeve should do.
        active_context: Optional list of active trigger names for runtime preview.
                        Example: ["Debugging Request", "Code Generation Request"]

    Returns:
        Compilation context with full block library, rules, and optional preview.
    """
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


# ── TOOL: inspect_active_state ────────────────────────────────────────────────
@mcp.tool()
def inspect_active_state(sleeve_json: str, active_context: list[str] = None) -> dict:
    """
    Given a sleeve and active context, show exactly what is ON and what is OFF.

    This is the primary runtime visibility tool. Shows which NeoStacks are
    active vs suppressed, which blocks are executing, and the full authority
    order of the active cognitive configuration.

    Args:
        sleeve_json: A compiled sleeve JSON string.
        active_context: List of active trigger names or contextual keywords.
                        Example: ["Debugging Request"]
                        Leave empty to see which stacks have no-gate (always-on) behavior.

    Returns:
        Full RuntimeSpec — the single truth object for this sleeve's state.
    """
    try:
        sleeve = json.loads(sleeve_json)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {str(e)}"}

    return _build_runtime_spec(sleeve, active_context or [])


# ── TOOL: generate_molt_map ───────────────────────────────────────────────────
@mcp.tool()
def generate_molt_map(sleeve_json: str, active_context: list[str] = None) -> dict:
    """
    Generate the MOLT Map — the cognitive envelope view.

    Answers: What is the AI supposed to be doing right now?
    Shows the active authority chain in order, what is suppressed and why,
    and the dominant directive governing the current cognitive state.

    Args:
        sleeve_json: A compiled sleeve JSON string.
        active_context: List of active trigger names or contextual keywords.

    Returns:
        MOLT Map with authority chain, active/suppressed blocks, and cognitive summary.
    """
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


# ── TOOL: generate_ir_graph ───────────────────────────────────────────────────
@mcp.tool()
def generate_ir_graph(sleeve_json: str, active_context: list[str] = None) -> dict:
    """
    Generate the IR (Intermediate Representation) routing graph.

    Answers: How did the system get here? Which stacks fired, which lost,
    which blocks are on the active route vs suppressed?

    The graph is a directed structure with node types:
      sleeve → neostack → neoblock → molt_block
      trigger_gate → neostack (activates or suppresses)

    Node states: active | suppressed | inactive | conflict

    Edge types: contains | routes_to | activates | suppresses | conflicts_with

    Args:
        sleeve_json: A compiled sleeve JSON string.
        active_context: List of active trigger names or contextual keywords.

    Returns:
        IR Graph with nodes, edges, active route, and suppressed routes.
    """
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


# ── TOOL: explain_route ───────────────────────────────────────────────────────
@mcp.tool()
def explain_route(sleeve_json: str, active_context: list[str] = None) -> dict:
    """
    Generate a human-readable explanation of the routing through a sleeve.

    Explains which NeoStacks fired and why, what blocks are active in what
    authority order, what is suppressed and what triggered the suppression.

    Args:
        sleeve_json: A compiled sleeve JSON string.
        active_context: List of active trigger names or contextual keywords.

    Returns:
        Plain language routing explanation with structured supporting data.
    """
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

    # Active stacks
    if spec["active_neostacks"]:
        lines.append(f"ACTIVE NEOSTACKS ({len(spec['active_neostacks'])}):")
        for ns in spec["active_neostacks"]:
            ev = next((e for e in spec["trigger_evaluations"]
                       if e["neostack"] == ns["name"]), {})
            lines.append(f"  ✓ {ns['name']} — {ev.get('reason', 'active')}")
    else:
        lines.append("ACTIVE NEOSTACKS: none — no triggers matched")

    lines.append("")

    # Suppressed stacks
    if spec["suppressed_neostacks"]:
        lines.append(f"SUPPRESSED NEOSTACKS ({len(spec['suppressed_neostacks'])}):")
        for ns in spec["suppressed_neostacks"]:
            lines.append(f"  ✗ {ns['name']} — {ns.get('reason', 'suppressed')}")
        lines.append("")

    # Active authority chain
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

    # Suppressed blocks
    if spec["suppressed_blocks_detail"]:
        lines.append(f"SUPPRESSED BLOCKS ({len(spec['suppressed_blocks_detail'])}):")
        for b in spec["suppressed_blocks_detail"][:8]:
            lines.append(f"  ✗ [{b['type']}] {b['name']} — {b['reason']}")
        if len(spec["suppressed_blocks_detail"]) > 8:
            lines.append(f"  ... and {len(spec['suppressed_blocks_detail'])-8} more")
        lines.append("")

    # Dominant directive
    if spec["dominant_directive"]:
        lines.append(f"DOMINANT DIRECTIVE: {spec['dominant_directive']}")
    lines.append(f"COGNITIVE SUMMARY: {mm.get('cognitive_summary', '')}")

    # Warnings
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


# ── TOOL: search_blocks ───────────────────────────────────────────────────────
@mcp.tool()
def search_blocks(
    query: str,
    block_type: str = None,
    limit: int = 20
) -> dict:
    """
    Search the canonical UMG block library by name or keyword.

    Args:
        query:      Search term — matches against block names
        block_type: Optional filter — TRIGGER | DIRECTIVE | INSTRUCTION |
                    SUBJECT | PRIMARY | PHILOSOPHY | BLUEPRINT | PERSONA
        limit:      Max results (default 20, max 100)

    Returns:
        Matching blocks with canonical IDs, types, names, and authority ranks.
    """
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
            score = (3 if name_lower.startswith(query_lower) else
                     2 if re.search(r'\b' + re.escape(query_lower), name_lower) else 1)
            results.append({
                **block,
                "authority_rank": AUTHORITY_RANK.get(block["type"], 99),
                "type_description": TYPE_DESCRIPTIONS.get(block["type"], ""),
                "_score": score
            })

    results.sort(key=lambda x: (x["_authority_rank"] if "_authority_rank" in x else x.get("authority_rank", 99), -x["_score"], x["name"]))
    clean = [{k: v for k, v in r.items() if k != "_score"} for r in results[:limit]]

    return {
        "query": query,
        "block_type_filter": block_type or "ALL",
        "total_matches": len(results),
        "showing": len(clean),
        "results": clean
    }


# ── TOOL: audit_sleeve ────────────────────────────────────────────────────────
@mcp.tool()
def audit_sleeve(sleeve_json: str) -> dict:
    """
    Audit a UMG sleeve JSON against the canonical block registry.

    Validates block names, type constraints, authority ordering, and
    governance alignment. Returns a structured audit report.

    Args:
        sleeve_json: A sleeve JSON string.

    Returns:
        Audit report with coverage score, issues, and governance status.
    """
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
            if gate.get("type") != "TRIGGER":
                issues.append(f"Gate '{gate.get('name')}' is not TRIGGER type")
            elif gate.get("name") not in NAME_IDX.get("TRIGGER", {}):
                issues.append(f"Unknown TRIGGER gate: '{gate.get('name')}'")
                custom_count += 1
            else:
                canonical_count += 1

        for nb in ns.get("neoBlocks", []):
            nb_types = set()
            blocks = nb.get("blocks", [])

            # Check authority ordering
            ranks = [AUTHORITY_RANK.get(b.get("type", ""), 99) for b in blocks]
            if ranks != sorted(ranks):
                issues.append(
                    f"NeoBlock '{nb.get('name')}' blocks are not in authority order "
                    f"(DIRECTIVE first). Current order: "
                    f"{' → '.join(b.get('type','?') for b in blocks)}"
                )

            for block in blocks:
                btype = block.get("type", "")
                bname = block.get("name", "")
                if btype == "TRIGGER":
                    issues.append(
                        f"TRIGGER '{bname}' inside NeoBlock '{nb.get('name')}' — "
                        "TRIGGERs belong in gates only"
                    )
                elif bname in NAME_IDX.get(btype, {}):
                    canonical_count += 1
                else:
                    issues.append(f"Non-canonical [{btype}]: '{bname}' in '{nb.get('name')}'")
                    custom_count += 1

                nb_types.add(btype)
                type_counts[btype] = type_counts.get(btype, 0) + 1

            if len(nb_types) < 2:
                issues.append(
                    f"NeoBlock '{nb.get('name')}' has only 1 block type — "
                    "mix ≥2 types for cognitive coverage"
                )

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
        "neoblocks": sum(
            len(ns.get("neoBlocks", [])) for ns in sleeve.get("neoStacks", [])
        ),
        "type_distribution": type_counts,
        "issues": issues,
        "governance": {
            "sovereign_review_required": custom_count > 0 or len(issues) > 0,
            "runtime_eligible": len(issues) == 0 and coverage >= 0.9,
            "source_mode": sleeve.get("provenance", {}).get("sourceMode", "unknown"),
            "provenance_note": (
                "Clean native — all blocks canonical, authority order correct"
                if len(issues) == 0 and custom_count == 0
                else f"{custom_count} non-canonical block(s), {len(issues)} issue(s) — review required"
            )
        }
    }


# ── TOOL: get_block_types ─────────────────────────────────────────────────────
@mcp.tool()
def get_block_types() -> dict:
    """
    Get an overview of all 8 UMG MOLT block types.

    Returns the canonical type system including authority ranks, descriptions,
    block counts, and sample blocks from each type.

    Returns:
        Complete MOLT type system reference.
    """
    return {
        "framework": "Universal Modular Generation (UMG)",
        "total_blocks": TOTAL,
        "version": "0.1.0",
        "sovereign": "NeoMAG",
        "license": "Apache-2.0",
        "authority_hierarchy_note": (
            "DIRECTIVE (rank 1) governs all blocks below it. "
            "PERSONA (rank 7) is a relational modifier. "
            "TRIGGER (rank 0) is a gate — never a body block."
        ),
        "types": {
            btype: {
                "prefix": LIBRARY[btype][0]["id"].split("-")[0],
                "authority_rank": AUTHORITY_RANK.get(btype, 99),
                "count": len(LIBRARY[btype]),
                "description": TYPE_DESCRIPTIONS[btype],
                "sample_blocks": [b["name"] for b in LIBRARY[btype][:5]],
                "role": (
                    "Gate only — activates NeoStack, never inside NeoBlock"
                    if btype == "TRIGGER"
                    else f"Body block — authority rank {AUTHORITY_RANK[btype]}"
                )
            }
            for btype in LIBRARY
        }
    }


# ── RUN ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
