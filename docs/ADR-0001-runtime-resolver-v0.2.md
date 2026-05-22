# ADR-0001 — UMG MCP Runtime Resolver v0.2

**Status:** Accepted  
**Sovereign:** NeoMAG  
**Date:** 2026-05-22  
**Authored by:** Claude (OG UMG Envoy) + MAG  

---

## Context

The UMG MCP Server currently supports basic block retrieval, static sleeve compilation,
and binary trigger gate matching. MOLT Map and IR Graph are generated as independent
tools from sleeve input rather than as projections of a unified runtime state.

The goal of v0.2 is to upgrade the server from a static block library into an
**action-capable UMG cognitive architecture runtime resolver** — one that accepts a
sleeve, active context, and options, then returns a full, traceable, modular runtime
state that describes exactly what cognitive architecture is active and why.

---

## Decisions

### D-01 — RuntimeSpec is the single source of truth

The `RuntimeSpec` object is the canonical output of every resolve call.

`MOLT Map` and `IR Graph` are **projections** of `RuntimeSpec`, not independent
systems. All current and future output tools must derive from `RuntimeSpec`.

Old tools (`inspect_active_state`, `generate_ir_graph`, `generate_molt_map`,
`explain_route`) retain their external signatures but will internally be refactored
to project from `RuntimeSpec` once the resolver is stable.

### D-02 — Gate priority activates; vertical hierarchy governs

Gate priority controls **activation order** — which stacks fire and in what sequence.

Vertical MOLT hierarchy controls **content dominance** — when active blocks conflict,
higher authority rank wins regardless of the priority of the gate that activated them.

These are orthogonal systems. They must not fight each other.

Rule: A high-priority gate may activate a Philosophy-level stack before a lower-priority
gate activates a Directive-level stack. But if those stacks conflict on content, the
Directive-level content governs.

Default vertical authority order:
1. Off / suppression metadata (highest override)
2. Trigger / route control
3. Directive
4. Instruction
5. Subject
6. Primary
7. Philosophy
8. Blueprint
9. Persona
10. Helper / local blocks (lowest)

### D-03 — Cross-type merge requires a declared composite MOLT type

Cross-type merge (combining blocks of different MOLT types) is **allowed** but only
when the merged output declares a composite MOLT type from the registry.

A `coherence_claim` is **evidence**, not authority. It is required but not sufficient.

Validation must resolve to one of:

| Path | Meaning |
|---|---|
| `declared_composite_match` | Composite type exists in registry and input types match |
| `rule_validated` | Resolver has a pre-approved safe pattern (e.g. DIR + INST = GovernedInstruction) |
| `sovereign_pending` | Plausible new composite, held for MAG review |
| `rejected` | Incoherent, undeclared, or unsafe merge |

Cross-type merge without a declared composite type **must fail** — no silent fallback.

### D-04 — coherence_claim is evidence, not authority

A merge specifying a `coherence_claim` has stated a reason. That reason must still
be validated. The claim cannot self-authorize a merge.

### D-05 — Threshold gate scoring uses gate-defined weights

`active_context.signals` remains simple — a flat array of binary string signals
(present = 1, absent = 0).

Threshold gates define `gate_weight` per condition. The resolver scores the gate by
summing the `gate_weight` values of all matched conditions.

```
score = Σ gate_weight of matched conditions
gate fires when score >= threshold
```

This keeps context portable. Different sleeves can interpret the same signal with
different importance. Scoring logic belongs to the gate, not the signal.

### D-06 — Declared type registry has two sections

`registry/declared_molt_types.json` contains:

```json
{
  "composite_molt_types": [],
  "output_composites": []
}
```

`composite_molt_types` — products of cross-type MOLT block merges. These have MOLT
authority behavior and participate in vertical hierarchy.

`output_composites` — products of `OutputBlueprintResolver`. These are Blueprint/output
format resolution products. They do **not** become base MOLT types.

The base MOLT type set remains stable:
`Trigger, Directive, Instruction, Subject, Primary, Philosophy, Blueprint, Persona, Merge, Off`

### D-07 — ID-only bundle deduplication in v0.2

When a bundle expands, blocks are deduplicated by **block ID only**.

Semantic overlap is not evaluated in v0.2. When two different block IDs may express
overlapping function, the resolver emits a `possible_semantic_overlap` warning but
does not suppress either block.

Semantic deduplication is deferred to Phase 3 or later.

### D-08 — CapabilityFrame ships prospective first

`CapabilityFrame.kind = "pre_response"` ships in v0.2.

The frame describes the intended active modular mind **before** response generation.

Schema room is added for `CapabilityFrame.kind = "post_response_trace"` but the
post-response trace layer is not implemented in v0.2 unless implementation cost is low.

### D-09 — Session state fields exist now; full session store is deferred

RuntimeSpec includes these fields in v0.2:

```json
{
  "session_id": "string | null",
  "turn_index": "number | null",
  "previous_runtime_id": "string | null",
  "stateful_features_enabled": false
}
```

Full session state (sequence gates, cooldown gates, continuity frames, runtime
evolution across turns) is deferred. These fields prevent a breaking schema change later.

### D-10 — route_trace[] is the primary debugging surface

Every deterministic resolver pass appends entries to `route_trace[]`.

No hidden logs. No separate explanation systems. The trace is native to RuntimeSpec.

Required passes (in execution order):

1. `gate_evaluation`
2. `vertical_resolution`
3. `bundle_expansion`
4. `merge_evaluation`
5. `lane_activation`
6. `output_blueprint_resolution`
7. `capability_frame_generation`
8. `molt_map_projection`
9. `ir_graph_projection`

Each trace entry must include: `pass`, `step_index`, `target_id`, `result`, `reason`,
and a pass-specific `inputs` object.

### D-11 — Backward compatibility: old MCP tool signatures are stable

The following tool external signatures must not change:

- `get_block_types`
- `search_blocks`
- `compile_sleeve`
- `audit_sleeve`
- `inspect_active_state`
- `generate_ir_graph`
- `generate_molt_map`
- `explain_route`

New v0.2 tools are added alongside. Internal refactoring to call `umg_resolve_runtime`
may happen after v0.2 tools are stable, but external contracts do not change.

### D-12 — Build small deterministic passes, not a monolithic resolver

The resolver is composed of discrete pass functions:

```
evaluateGates()
resolveVerticalHierarchy()
expandBundles()
evaluateMerges()
activateHorizontalLanes()
resolveOutputBlueprint()
composeCapabilityFrame()
projectMoltMap()
projectIrGraph()
```

Each pass receives the current `RuntimeSpec` draft state, updates it, and appends
trace entries. No pass should perform the work of another pass.

---

## Implementation Order

**Phase 0** — This ADR  
**Phase 1** — Schema pack (9 schemas, listed below)  
**Phase 2a** — Gate engine + vertical dominance (together, not separated)  
**Phase 2b** — Inline bundle expansion  
**Phase 2c** — Declared composite registry + merge engine  
**Phase 2d** — Horizontal lanes + OutputBlueprintResolver  
**Phase 2e** — CapabilityFrame (prospective)  
**Phase 3** — MOLT Map + IR Graph as RuntimeSpec projections  
**Phase 4** — MCP tool exposure (v0.2 tools)  
**Phase 5** — Tests (see acceptance criteria)  
**Phase 6** — Claude plugin packaging  

---

## Schema Pack (Phase 1)

Produced in dependency order:

1. `schemas/umg-runtime-spec.schema.json`
2. `schemas/umg-gate-expr.schema.json`
3. `schemas/umg-declared-molt-types.schema.json`
4. `schemas/umg-merge-spec.schema.json`
5. `schemas/umg-bundle.schema.json`
6. `schemas/umg-capability-frame.schema.json`
7. `schemas/umg-output-blueprint-resolution.schema.json`
8. `schemas/umg-ir-graph.schema.json`
9. `schemas/umg-molt-map.schema.json`

---

## Acceptance Criteria

**Test 1 — Runtime state**: Sleeve with three stacks (governance, technical analysis,
creative) + context `["technical_request", "governance_review"]` returns governance
active, technical analysis active, creative suppressed, with reason codes, MOLT Map,
and IR Graph.

**Test 2 — Cross-type merge (valid)**: DIR "Honor governance" + INST "Perform technical
audit" with `merged_molt_type: "GovernedInstruction"` returns coherent merge, directive
governs instruction, merge node in IR Graph.

**Test 3 — Cross-type merge (invalid)**: Cross-type merge without declared composite
type returns `rejected` with `reason: "missing_declared_composite_molt_type"`.
No silent fallback.

**Test 4 — Bundle expansion**: Governance bundle used by two stacks returns bundle
expanded once, duplicate blocks deduped by ID, provenance preserved, graph shows
expansion node.

**Test 5 — Capability Frame flex**: Same sleeve, different contexts produce different
active frames. `technical_request` → analysis + audit + planning lanes.
`creative_request` → creative + output + planning lanes.

---

## Consequences

- RuntimeSpec becomes a non-trivial object. Callers who previously called individual
  tools will need to call `umg_resolve_runtime` and project what they need.
- Old tools remain stable but are now maintained as thin projections — their
  correctness depends on the resolver.
- The `declared_molt_types.json` registry becomes a governed artifact. Adding composite
  types requires either `rule_validated` match or `sovereign_pending` review.
- Session state fields add schema overhead now but save a breaking change later.

---

*This ADR is locked. Do not reopen architecture decisions recorded here.*  
*Amendments require a new ADR (ADR-0002+) with explicit sovereign review.*
