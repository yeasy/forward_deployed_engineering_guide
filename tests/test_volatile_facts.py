#!/usr/bin/env python3
"""Contracts for the volatile-facts ledger and its build gate.

The ledger exists because this book previously stamped eight files with
`截至 2026-05-18` — a date that, per this repository's own git history, was 33
days *after* those files were written and was later harmonized downward for
editorial tidiness. A stamp nobody is forced to re-earn decays into decoration.
These tests pin the mechanism that forces it to be re-earned.
"""

from __future__ import annotations

import re
import sys
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "appendix/volatile_facts.md"

sys.path.insert(0, str(ROOT))

import check_project_rules  # noqa: E402


class VolatileFactsLedgerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.text = LEDGER.read_text(encoding="utf-8")

    def test_checker_exposes_the_gate(self) -> None:
        self.assertTrue(
            callable(getattr(check_project_rules, "check_volatile_facts", None)),
            "check_project_rules.py must expose check_volatile_facts()",
        )

    def test_ledger_passes_its_own_gate_today(self) -> None:
        self.assertEqual([], check_project_rules.check_volatile_facts())

    def test_header_is_internally_consistent(self) -> None:
        match = re.search(
            r"`verified_at`:\s*(\d{4}-\d{2}-\d{2})\s*·\s*"
            r"`expires_at`:\s*(\d{4}-\d{2}-\d{2})\s*·\s*"
            r"`ttl_days`:\s*(\d+)",
            self.text,
        )
        self.assertIsNotNone(match, "ledger header must carry all three fields")
        verified = date.fromisoformat(match.group(1))
        expires = date.fromisoformat(match.group(2))
        ttl = int(match.group(3))
        self.assertEqual(timedelta(days=ttl), expires - verified)
        low, high = check_project_rules.VOLATILE_TTL_BOUNDS
        self.assertTrue(low <= ttl <= high, f"ttl_days {ttl} outside {low}-{high}")

    def test_gate_fails_once_the_snapshot_expires(self) -> None:
        """The whole point: an untouched ledger must eventually break the build."""
        expires = date.fromisoformat(
            re.search(r"`expires_at`:\s*(\d{4}-\d{2}-\d{2})", self.text).group(1)
        )
        issues = check_project_rules.check_volatile_facts(today=expires + timedelta(days=1))
        self.assertTrue(
            any("expired" in issue for issue in issues),
            f"an expired ledger must fail the gate, got: {issues}",
        )

    def test_gate_rejects_a_ttl_that_does_not_match_the_dates(self) -> None:
        broken = self._ledger_with(
            self.text.replace("`ttl_days`: 45", "`ttl_days`: 40")
        )
        issues = check_project_rules.check_volatile_facts(filepath=broken)
        self.assertTrue(
            any("expires_at must be" in issue for issue in issues), issues
        )

    def test_gate_rejects_an_out_of_band_ttl(self) -> None:
        low, high = check_project_rules.VOLATILE_TTL_BOUNDS
        text = self.text.replace("`ttl_days`: 45", f"`ttl_days`: {high + 300}")
        text = re.sub(r"`expires_at`: \d{4}-\d{2}-\d{2}", "`expires_at`: 2027-05-25", text)
        issues = check_project_rules.check_volatile_facts(filepath=self._ledger_with(text))
        self.assertTrue(any("ttl_days must be between" in issue for issue in issues), issues)

    def test_gate_rejects_an_unresolved_conflict(self) -> None:
        broken = self._ledger_with(
            self.text.replace("status=current", "status=open-conflict")
        )
        issues = check_project_rules.check_volatile_facts(filepath=broken)
        self.assertTrue(any("unresolved conflict" in issue for issue in issues), issues)

    def test_gate_rejects_a_missing_status_marker(self) -> None:
        broken = self._ledger_with(
            re.sub(r"<!-- volatile-status:[^>]*-->", "", self.text)
        )
        issues = check_project_rules.check_volatile_facts(filepath=broken)
        self.assertTrue(any("Missing volatile-status" in issue for issue in issues), issues)

    def test_ledger_bridges_to_the_claim_ledger_without_duplicating_it(self) -> None:
        """The two tables must stay complementary, not become two copies of one."""
        self.assertIn("claim_ledger.md", self.text, "the bridge row must link the claim ledger")
        self.assertTrue((ROOT / "appendix/claim_ledger.md").is_file())
        claim_ids = set(re.findall(r"FDE-14\.\d-\d{3}", self.text))
        self.assertEqual(
            set(),
            claim_ids,
            f"case numbers belong in claim_ledger.md only; found {sorted(claim_ids)}",
        )

    def test_ledger_is_reachable_from_summary_and_appendix_index(self) -> None:
        for path in (ROOT / "SUMMARY.md", ROOT / "appendix/README.md"):
            with self.subTest(path=path.name):
                self.assertIn("volatile_facts.md", path.read_text(encoding="utf-8"))

    def test_every_row_carries_all_five_columns(self) -> None:
        rows = [
            line
            for line in self.text.splitlines()
            if line.startswith("|") and not re.match(r"^\|[\s\-:|]+\|$", line)
        ]
        self.assertGreaterEqual(len(rows), 6, "expected a header plus the category rows")
        for row in rows:
            with self.subTest(row=row[:40]):
                cells = [c for c in row.strip().strip("|").split(" | ")]
                self.assertEqual(
                    5,
                    len(cells),
                    "each row needs 类别 / 当前维护口径 / 权威入口 / 复核节奏 / 编辑要求",
                )

    def test_no_file_still_claims_the_retired_house_wide_snapshot_date(self) -> None:
        """`截至 2026-05-18` was never a verification date — see the module docstring."""
        offenders = sorted(
            str(p.relative_to(ROOT))
            for p in ROOT.rglob("*.md")
            if ".git" not in p.parts and "截至 2026-05-18" in p.read_text(encoding="utf-8")
        )
        self.assertEqual(
            [],
            offenders,
            "these files carry a stamp that predates their own content; point them"
            f" at appendix/volatile_facts.md instead: {offenders}",
        )

    def _ledger_with(self, text: str) -> Path:
        import tempfile

        tmp = Path(tempfile.mkstemp(suffix=".md")[1])
        tmp.write_text(text, encoding="utf-8")
        self.addCleanup(tmp.unlink)
        return tmp


if __name__ == "__main__":
    unittest.main()
