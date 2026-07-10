from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CAPSTONE = ROOT / "appendix" / "capstone.md"


class CapstoneContractTests(unittest.TestCase):
    def text(self) -> str:
        self.assertTrue(CAPSTONE.is_file(), CAPSTONE)
        return CAPSTONE.read_text(encoding="utf-8")

    def test_ten_deliverables_total_exactly_one_hundred_points(self):
        text = self.text()
        deliverables = re.findall(
            r"<!-- capstone-deliverable: id=(CAP-\d{2}) points=(\d{1,2}) -->",
            text,
        )
        self.assertEqual(len(deliverables), 10)
        self.assertEqual(len({item[0] for item in deliverables}), 10)
        self.assertEqual(sum(int(item[1]) for item in deliverables), 100)
        self.assertIn("总分：100 分", text)

    def test_one_scenario_runs_from_discovery_to_client_handoff(self):
        text = self.text()
        stages = re.findall(r"<!-- capstone-stage: ([a-z-]+) -->", text)
        self.assertEqual(
            stages,
            [
                "discovery",
                "framing",
                "architecture",
                "pilot",
                "production",
                "operations",
                "client-handoff",
            ],
        )
        for marker in (
            "同一个连贯场景",
            "异常订单重排建议",
            "客户接管演练",
            "从 Discovery 到客户接管",
        ):
            self.assertIn(marker, text)

    def test_hard_fail_conditions_override_score(self):
        text = self.text()
        hard_fails = re.findall(r"<!-- capstone-hard-fail: id=(HF-\d{2}) -->", text)
        self.assertGreaterEqual(len(hard_fails), 6)
        self.assertEqual(len(hard_fails), len(set(hard_fails)))
        for marker in (
            "任一项触发即不得通过",
            "未授权客户数据或 secret",
            "没有回滚",
            "供应商结果数字",
            "客户无法独立",
        ):
            self.assertIn(marker, text)

    def test_capstone_and_ledger_are_routed_from_reader_entry_points(self):
        routes = {
            "README.md": ("appendix/capstone.md", "appendix/claim_ledger.md"),
            "SUMMARY.md": ("appendix/capstone.md", "appendix/claim_ledger.md"),
            "appendix/README.md": ("capstone.md", "claim_ledger.md"),
            "appendix/templates.md": ("capstone.md", "claim_ledger.md"),
        }
        for relative, markers in routes.items():
            text = (ROOT / relative).read_text(encoding="utf-8")
            for marker in markers:
                self.assertIn(marker, text, relative)


if __name__ == "__main__":
    unittest.main()
