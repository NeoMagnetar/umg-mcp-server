# UMG MCP Server Phase 2a Handoff

## Branch
`feature/v0.2-phase2a-gate-engine`

## Commit message
```text
feat: implement Phase 2a gate engine and vertical hierarchy preview
```

## PR Title
```text
feat: UMG Runtime Resolver v0.2 — Phase 2a gate engine and vertical hierarchy
```

## PR Body
```markdown
## Summary

Implements Phase 2a of the UMG Runtime Resolver v0.2 upgrade in the MCP server.

This change adds the first deterministic resolver passes:
- `evaluate_gates()`
- `resolve_vertical_hierarchy()`

It also exposes a new preview MCP tool:
- `umg_preview_gate_eval`

The implementation follows ADR-0001 and the v0.2 schemas already merged into the repo.

## What's included

### New pass functions
- `evaluate_gates(runtime_spec, sleeve, active_context)`
- `resolve_vertical_hierarchy(runtime_spec, sleeve)`

### Gate operators implemented
All 6 operators defined in `schemas/umg-gate-expr.schema.json` are handled:
- `any`
- `all`
- `not`
- `threshold`
- `priority`
- `fallback`

Threshold scoring follows ADR-0001 D-05 exactly:
- `score = sum(gate_weight for matched conditions)`
- gate fires when `score >= threshold`

### Runtime output surfaces
The preview tool returns:
- `runtime_id`
- `sleeve_id`
- `sleeve_name`
- `source_mode`
- `active_context`
- `gate_evaluations[]`
- `active_stacks[]`
- `active_blocks[]`
- `suppressed_items[]`
- `conflicts[]`
- `vertical_resolution`
- `route_trace[]`

### route_trace support
Both implemented passes append deterministic trace entries with:
- `pass`
- `step_index`
- `target_id`
- `result`
- `reason`
- `inputs`

### MCP tool exposure
Added `umg_preview_gate_eval` in the same FastMCP registration style as the existing tools.

### Reference test fixture
Added:
- `phase2a_reference_sleeve.json`

### Acceptance tests
Added 5 explicit tests in `test_phase2a.py` covering:
1. governance + technical active, creative suppressed
2. exact threshold scoring formula
3. all-gate missing-signal suppression
4. fallback activation when nothing else matches
5. vertical hierarchy suppression of lower-priority same-type content

## Notes / constraints
- Existing MCP tool signatures were left unchanged.
- This is a Phase 2a preview surface, not a full end-to-end resolver.
- The current vertical hierarchy implementation resolves same-type conflicts by rank, then stack priority.
- The earlier v0.1 legacy runtime path remains present for backward compatibility.

## Verification
```text
python -m unittest test_phase2a.py
```

## Reviewer
@NeoMagnetar — sovereign review required before merge.
```
