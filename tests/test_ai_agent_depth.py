from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
NEW_RULES = {
    "AI.CONTEXT.002",
    "AI.CONTEXT.003",
    "AI.CONTEXT.004",
    "AI.CONTEXT.005",
    "AI.PRIVACY.001",
    "AI.EVAL.002",
    "AI.CHANGE.002",
}


class AIAgentDepthTests(unittest.TestCase):
    def test_rule_pack_adds_explicit_depth_without_changing_identity(self) -> None:
        pack = yaml.safe_load(
            (ROOT / "resources/rules/ai-agent-core.yaml").read_text(encoding="utf-8")
        )
        self.assertEqual(pack["id"], "ai-agent-core")
        self.assertEqual(pack["review_kind"], "ai-agent")
        self.assertEqual(pack["version"], "1.1.0")
        rule_ids = {rule["id"] for rule in pack["rules"]}
        self.assertTrue(rule_ids >= NEW_RULES)
        self.assertEqual(len(rule_ids), len(pack["rules"]))
        for rule in pack["rules"]:
            if rule["id"] in NEW_RULES:
                evidence = " ".join(rule["evidence_requirements"]).lower()
                self.assertIn("critical flow", evidence)

    def test_skill_preserves_candidate_handoff_and_public_name(self) -> None:
        skill = (ROOT / "skills/ai-agent-architecture-audit/SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertEqual(skill.splitlines()[1], "name: ai-agent-architecture-audit")
        self.assertLess(len(skill.splitlines()), 500)
        self.assertIn("verification.status: candidate", skill)
        self.assertIn("technology names only as versioned evidence", skill)
        self.assertIn("Do not load every", skill)
        self.assertIn("candidate-driving claim", skill)

    def test_reference_documents_each_bundled_rule_once(self) -> None:
        pack = yaml.safe_load(
            (ROOT / "resources/rules/ai-agent-core.yaml").read_text(encoding="utf-8")
        )
        reference = (ROOT / "resources/references/ai-agent-rules.md").read_text(
            encoding="utf-8"
        )
        rows = [
            [cell.strip() for cell in line.strip("|").split("|")]
            for line in reference.splitlines()
            if line.startswith("| `AI.")
        ]
        rule_ids = [row[0].strip("`") for row in rows]
        self.assertEqual(set(rule_ids), {rule["id"] for rule in pack["rules"]})
        self.assertEqual(len(rule_ids), len(set(rule_ids)))
        for row in rows:
            with self.subTest(rule_id=row[0]):
                self.assertEqual(len(row), 3)
                self.assertTrue(row[1], "Rule domain is missing")
                self.assertTrue(row[2], "Rule invariant is missing")


if __name__ == "__main__":
    unittest.main()
