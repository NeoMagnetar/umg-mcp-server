import unittest

import main


class Phase2AFinalTests(unittest.TestCase):
    def test_directives_are_peers_not_suppressed(self):
        sleeve = {"sleeve_name": "T", "neoStacks": [
            {"name": "S1", "gates": [], "neoBlocks": [{"name": "B1", "blocks": [
                {"type": "DIRECTIVE", "name": "Honor Governance"},
                {"type": "DIRECTIVE", "name": "Assess Accurately"},
            ]}]}]}
        r = main._run_phase2a_preview(sleeve, [])
        ad = r["vertical_resolution"]["active_by_rank"]["Directive"]
        assert "Honor Governance" in ad and "Assess Accurately" in ad
        assert len(r["vertical_resolution"]["cross_rank_conflicts"]) == 0

    def test_cross_rank_conflict_directive_governs_blueprint(self):
        sleeve = {"sleeve_name": "T", "neoStacks": [
            {"name": "S1", "gates": [], "neoBlocks": [{"name": "B1", "blocks": [
                {"type": "DIRECTIVE", "name": "Honor Governance"},
                {"type": "BLUEPRINT", "name": "Bypass Governance Constraints"},
            ]}]}]}
        r = main._run_phase2a_preview(sleeve, [])
        c = r["vertical_resolution"]["cross_rank_conflicts"]
        assert len(c) == 1 and c[0]["winner_block"] == "Honor Governance"

    def test_off_block_suppresses_target(self):
        sleeve = {"sleeve_name": "T", "neoStacks": [
            {"name": "S1", "gates": [], "neoBlocks": [{"name": "B1", "blocks": [
                {"type": "DIRECTIVE", "name": "Honor Governance"},
                {"type": "Off", "name": "Honor Governance"},
            ]}]}]}
        r = main._run_phase2a_preview(sleeve, [])
        assert len(r["vertical_resolution"]["off_suppressed"]) > 0

    def test_compile_sleeve_returns_complete_sleeve(self):
        r = main.compile_sleeve("debugging code agent")
        assert "sleeve_json" in r and "neoStacks" in r["sleeve_json"]
        stacks = r["sleeve_json"]["neoStacks"]
        assert any(not s.get("gates") for s in stacks)
        for s in stacks:
            for nb in s.get("neoBlocks", []):
                assert "DIRECTIVE" in [b["type"] for b in nb.get("blocks", [])]

    def test_compile_sleeve_no_raw_library_dump(self):
        r = main.compile_sleeve("planning agent")
        assert "canonical_library" not in r and "all_blocks" not in r

    def test_build_neostack_debugging(self):
        r = main.umg_build_neostack(
            purpose="trace and isolate code bugs",
            always_on=False,
            gate_signals='["debugging_request"]',
            block_count=5,
        )
        ns = r["neostack_json"]
        types = [b["type"] for b in ns["neoBlocks"][0]["blocks"]]
        assert "DIRECTIVE" in types and "INSTRUCTION" in types
        assert len(ns["gates"]) >= 1

    def test_build_neostack_always_on_no_gate(self):
        r = main.umg_build_neostack(purpose="governance core", always_on=True)
        assert r["neostack_json"]["gates"] == []

    def test_search_blocks_batch_dedupe(self):
        r = main.search_blocks(queries='["debug","root cause","trace causality"]', limit_per_query=3)
        assert r["mode"] == "batch"
        keys = [b.get("block_id") or b.get("id") or b.get("name") for b in r["flat_results"]]
        assert len(keys) == len(set(keys))

    def test_search_blocks_single_mode_unchanged(self):
        r = main.search_blocks(query="debug", limit=5)
        assert r.get("mode", "single") != "batch"

    def test_compile_sleeve_alignment_fields_present(self):
        r = main.compile_sleeve("debugging code agent")
        for f in ["selection_result", "runtime_spec_fragment", "ir_matrix_rows", "trace_events", "assembly_source"]:
            assert f in r

    def test_runtime_spec_fragment_unresolved(self):
        r = main.compile_sleeve("debugging code agent")
        f = r["runtime_spec_fragment"]
        assert f["resolved"] is False
        assert f["resolution_stage"] == "assembly"
        assert f["requires_resolver"] is True

    def test_ir_rows_assembly_states_only(self):
        r = main.compile_sleeve("debugging code agent")
        allowed = {"assembled", "candidate", "pending_eval", "unresolved"}
        forbidden = {"active", "suppressed", "blocked", "passed", "failed", "executed", "completed"}
        for row in r["ir_matrix_rows"]:
            assert row.get("state") in allowed
            assert row.get("state") not in forbidden
            assert row.get("resolution_state") == "unresolved"

    def test_gates_pending_eval_at_assembly(self):
        r = main.compile_sleeve("debugging code agent")
        for row in r["ir_matrix_rows"]:
            if row.get("layer") == "gate":
                assert row.get("gate_eval_state") == "pending_eval"

    def test_assembly_tools_do_not_claim_execution(self):
        r = main.compile_sleeve("update README documentation")
        for k in ["tool_result", "tool_results", "execution_result"]:
            assert k not in r
        for row in r.get("ir_matrix_rows", []):
            assert row.get("state") not in {"executed", "completed"}

    def test_no_merge_or_off_as_molt_type(self):
        r = main.compile_sleeve("debugging code agent")
        for s in r["sleeve_json"]["neoStacks"]:
            for nb in s.get("neoBlocks", []):
                for b in nb.get("blocks", []):
                    assert b.get("type") not in {"Merge", "Off"}
                    assert b.get("molt_type", b.get("type")) not in {"Merge", "Off"}


if __name__ == "__main__":
    unittest.main()
