import json
import pathlib
import unittest

import main

ROOT = pathlib.Path(__file__).resolve().parent
REFERENCE_SLEEVE = json.loads((ROOT / 'phase2a_reference_sleeve.json').read_text(encoding='utf-8'))


class Phase2AAcceptanceTests(unittest.TestCase):
    def test_runtime_state_governance_and_technical_active_creative_suppressed(self):
        result = main._run_phase2a_preview(REFERENCE_SLEEVE, ["technical_request", "governance_review"])
        active_stack_ids = [s["stack_id"] for s in result["active_stacks"]]
        self.assertEqual(active_stack_ids, ["NS-GOV", "NS-TECH"])

        gate_results = {g["gate_id"]: g for g in result["gate_evaluations"]}
        self.assertEqual(gate_results["GATE_GOV_THRESHOLD"]["result"], "activated")
        self.assertEqual(gate_results["GATE_GOV_THRESHOLD"]["score"], 0.75)
        self.assertEqual(gate_results["GATE_ANY_TECH"]["result"], "activated")
        self.assertEqual(gate_results["GATE_NOT_CREATIVE"]["result"], "suppressed")
        self.assertIn("governance_review", gate_results["GATE_NOT_CREATIVE"]["reason"])

        suppressed_ids = {item["id"] for item in result["suppressed_items"]}
        self.assertIn("NS-CREATIVE", suppressed_ids)
        self.assertTrue(any(entry["pass"] == "gate_evaluation" for entry in result["route_trace"]))
        self.assertTrue(any(entry["pass"] == "vertical_resolution" for entry in result["route_trace"]))

    def test_threshold_gate_exact_formula(self):
        result = main._run_phase2a_preview(REFERENCE_SLEEVE, ["technical_request", "architecture_design"])
        gate = next(g for g in result["gate_evaluations"] if g["gate_id"] == "GATE_GOV_THRESHOLD")
        self.assertEqual(gate["score"], 0.65)
        self.assertEqual(gate["threshold"], 0.75)
        self.assertEqual(gate["result"], "suppressed")
        self.assertEqual(gate["matched_conditions"], ["technical_request", "architecture_design"])
        self.assertIn("below required 0.75", gate["reason"])

    def test_all_gate_requires_all_signals(self):
        result = main._run_phase2a_preview(REFERENCE_SLEEVE, ["governance_review", "audit_request"])
        gate = next(g for g in result["gate_evaluations"] if g["gate_id"] == "GATE_ALL_RELEASE")
        self.assertEqual(gate["result"], "suppressed")
        self.assertEqual(gate["failed_conditions"], ["output_required"])
        self.assertIn("output_required", gate["reason"])

    def test_fallback_gate_activates_when_nothing_else_matches(self):
        result = main._run_phase2a_preview(REFERENCE_SLEEVE, ["unrelated_signal"])
        active_stack_ids = [s["stack_id"] for s in result["active_stacks"]]
        self.assertEqual(active_stack_ids, ["NS-DEFAULT"])
        gate = next(g for g in result["gate_evaluations"] if g["gate_id"] == "GATE_DEFAULT_GOVERNANCE")
        self.assertEqual(gate["result"], "fallback_activated")
        self.assertEqual(gate["matched"], True)
        self.assertEqual(gate["reason"], "No gate matched - fallback activated.")

    def test_vertical_hierarchy_suppresses_lower_priority_same_type_block(self):
        result = main._run_phase2a_preview(REFERENCE_SLEEVE, ["technical_request", "governance_review"])
        active_directives = [b for b in result["active_blocks"] if b["molt_type"] == "DIRECTIVE"]
        self.assertEqual(len(active_directives), 1)
        self.assertEqual(active_directives[0]["block_id"], "DIR-GOV")

        suppressed = [item for item in result["suppressed_items"] if item["id"] == "DIR-TECH"]
        self.assertEqual(len(suppressed), 1)
        self.assertEqual(suppressed[0]["suppression_reason"], "higher_vertical_authority")
        self.assertEqual(suppressed[0]["suppressed_by_id"], "DIR-GOV")
        self.assertTrue(any(c["winner_id"] == "DIR-GOV" for c in result["conflicts"]))


if __name__ == '__main__':
    unittest.main()
