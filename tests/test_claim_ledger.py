from __future__ import annotations

import re
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "appendix" / "claim_ledger.md"
CASE_FILES = tuple(ROOT.glob("14_cases/14.[1-6]_*.md"))
CLAIM_ID = re.compile(r"FDE-14\.([1-6])-\d{3}")
ALLOWED_TYPES = {
    "institutional-claim",
    "vendor-claim",
    "research-result",
    "regulatory-finding",
    "reported-outcome",
    "synthetic-pattern",
}


def ledger_rows(text: str) -> list[dict[str, str]]:
    rows = []
    for line in text.splitlines():
        if not re.match(r"^\|\s*FDE-14\.[1-6]-\d{3}\s*\|", line):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 7:
            raise AssertionError(f"ledger row has {len(cells)} cells: {line}")
        rows.append(dict(zip(("id", "chapter", "type", "claim", "source", "verified", "boundary"), cells)))
    return rows


class ClaimLedgerTests(unittest.TestCase):
    def text(self) -> str:
        self.assertTrue(LEDGER.is_file(), LEDGER)
        return LEDGER.read_text(encoding="utf-8")

    def test_ledger_has_unique_complete_typed_rows(self):
        text = self.text()
        rows = ledger_rows(text)
        self.assertGreaterEqual(len(rows), 14)
        ids = [row["id"] for row in rows]
        self.assertEqual(len(ids), len(set(ids)))
        for row in rows:
            self.assertRegex(row["id"], CLAIM_ID)
            self.assertEqual(row["chapter"], f"14.{CLAIM_ID.fullmatch(row['id']).group(1)}")
            self.assertIn(row["type"], ALLOWED_TYPES)
            self.assertTrue(row["claim"])
            self.assertRegex(row["source"], r"\[.+\]\(https://[^)]+\)")
            self.assertTrue(row["boundary"])

    def test_verified_at_is_a_real_past_iso_date(self, today: date | None = None) -> None:
        """`verified_at` must be re-earned, not re-typed.

        This deliberately does NOT pin a literal date. Pinning one makes the test
        fail on every legitimate re-verification, which teaches whoever is refreshing
        the ledger to edit the number until the suite goes green — the opposite of
        what the stamp is for. It also does not expire: per the ledger's own header,
        this table is a historical record and `appendix/volatile_facts.md` is the
        clock. What is actually checkable here is that each stamp is a real ISO date
        that has already happened.
        """
        today = today or date.today()
        for row in ledger_rows(self.text()):
            self.assertRegex(row["verified"], r"^\d{4}-\d{2}-\d{2}$", row["id"])
            stamped = date.fromisoformat(row["verified"])
            self.assertLessEqual(stamped, today, f"{row['id']} is stamped in the future")

    def test_every_case_chapter_claim_id_is_in_ledger_and_vice_versa(self):
        rows = ledger_rows(self.text())
        ledger_ids = {row["id"] for row in rows}
        chapter_ids: list[str] = []
        self.assertEqual(len(CASE_FILES), 6)
        for path in CASE_FILES:
            ids = re.findall(r"<!-- claim-id: (FDE-14\.[1-6]-\d{3}) -->", path.read_text(encoding="utf-8"))
            self.assertTrue(ids, path)
            chapter_ids.extend(ids)
        self.assertEqual(len(chapter_ids), len(set(chapter_ids)))
        self.assertEqual(set(chapter_ids), ledger_ids)

    def test_vendor_outcomes_are_never_local_acceptance_targets(self):
        text = self.text()
        self.assertIn("vendor-claim 的结果数字不得转为本地验收目标", text)
        vendor_rows = [row for row in ledger_rows(text) if row["type"] == "vendor-claim"]
        self.assertGreaterEqual(len(vendor_rows), 4)
        for row in vendor_rows:
            self.assertIn("不得转为本地目标", row["boundary"], row["id"])


if __name__ == "__main__":
    unittest.main()
