#!/usr/bin/env python3
"""Lightweight Markdown project checks for book repositories."""

from __future__ import annotations

import re
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote, urlparse


ROOT = Path(__file__).resolve().parent
SKIP_DIRS = {
    ".agent",
    ".git",
    ".github",
    ".idea",
    ".mdpress",
    ".mdpress_temp",
    ".mypy_cache",
    ".obsidian",
    ".playwright-cli",
    ".pytest_cache",
    ".vuepress",
    "__pycache__",
    "_book",
    "dist",
    "mcp_cache",
    "node_modules",
    "output",
}
SKIP_PREFIXES = ("_site",)
HTML_TARGET_RE = re.compile(
    r"\b(?:href|src)\s*=\s*(?:\"([^\"]*)\"|'([^']*)'|([^\s>]+))",
    re.IGNORECASE,
)
FENCE_RE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")

VOLATILE_FACTS = ROOT / "appendix/volatile_facts.md"
# The ledger's own TTL is read from its header rather than hardcoded here: this
# book cites mostly standards and specs, which move far slower than the
# product-and-pricing surface a sibling book tracks, so pinning it to a sibling's
# cadence would fire the gate on material that provably cannot have moved — and
# a gate that cries wolf teaches the maintainer to bump the date without looking.
VOLATILE_TTL_BOUNDS = (30, 60)


def check_volatile_facts(filepath=VOLATILE_FACTS, today=None):
    """Fail the build once the dated snapshot of volatile external facts expires."""
    path = Path(filepath)
    current_date = today or date.today()
    issues = []

    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"{path} [Volatile facts] Cannot read ledger: {exc}"]

    metadata = re.search(
        r"`verified_at`:\s*(\d{4}-\d{2}-\d{2})\s*·\s*"
        r"`expires_at`:\s*(\d{4}-\d{2}-\d{2})\s*·\s*"
        r"`ttl_days`:\s*(\d+)",
        content,
    )
    if metadata is None:
        return [
            f"{path} [Volatile facts] Missing verified_at, expires_at, or ttl_days metadata."
        ]

    try:
        verified_at = datetime.strptime(metadata.group(1), "%Y-%m-%d").date()
        expires_at = datetime.strptime(metadata.group(2), "%Y-%m-%d").date()
        ttl_days = int(metadata.group(3))
    except ValueError as exc:
        return [f"{path} [Volatile facts] Invalid metadata: {exc}"]

    low, high = VOLATILE_TTL_BOUNDS
    if not low <= ttl_days <= high:
        issues.append(
            f"{path} [Volatile facts] ttl_days must be between {low} and {high}, got {ttl_days}."
        )
    if expires_at - verified_at != timedelta(days=ttl_days):
        issues.append(
            f"{path} [Volatile facts] expires_at must be verified_at plus ttl_days"
            f" ({ttl_days} days); got {verified_at} to {expires_at}."
        )
    if verified_at > current_date:
        issues.append(
            f"{path} [Volatile facts] verified_at is in the future: {verified_at}."
        )
    if current_date > expires_at:
        issues.append(
            f"{path} [Volatile facts] Snapshot expired on {expires_at}; recheck the"
            " authoritative entry points before bumping the date."
        )

    statuses = re.findall(
        r"<!--\s*volatile-status:\s+id=[^\s]+\s+status=([^\s]+)\s*-->",
        content,
    )
    if not statuses:
        issues.append(f"{path} [Volatile facts] Missing volatile-status marker.")
    for status in statuses:
        if status == "open-conflict":
            issues.append(f"{path} [Volatile facts] Ledger has an unresolved conflict.")
        elif status not in {"current", "resolved-conflict"}:
            issues.append(
                f"{path} [Volatile facts] Unsupported volatile-status: {status}."
            )

    return issues


def should_skip(path: Path) -> bool:
    return any(
        part in SKIP_DIRS or part.startswith(SKIP_PREFIXES)
        for part in path.relative_to(ROOT).parts
    )


def iter_markdown_files() -> list[Path]:
    return sorted(path for path in ROOT.rglob("*.md") if not should_skip(path))


def strip_fenced_blocks(text: str) -> str:
    output: list[str] = []
    in_fence = False
    fence_marker = ""
    fence_len = 0
    for line in text.splitlines():
        match = FENCE_RE.match(line)
        if match:
            marker = match.group(1)
            char = marker[0]
            length = len(marker)
            if not in_fence:
                in_fence = True
                fence_marker = char
                fence_len = length
            elif char == fence_marker and length >= fence_len:
                in_fence = False
            output.append("")
            continue
        output.append("" if in_fence else line)
    return "\n".join(output)


def check_fences(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    open_fence: tuple[str, int, int] | None = None
    for line_no, line in enumerate(text.splitlines(), 1):
        match = FENCE_RE.match(line)
        if not match:
            continue
        marker = match.group(1)
        char = marker[0]
        length = len(marker)
        if open_fence is None:
            open_fence = (char, length, line_no)
            continue
        open_char, open_len, _ = open_fence
        if char == open_char and length >= open_len:
            open_fence = None
    if open_fence is not None:
        _, _, line_no = open_fence
        issues.append(f"{path.relative_to(ROOT)}:{line_no}: unclosed fenced code block")
    return issues


def is_local_target(raw_target: str) -> bool:
    parsed = urlparse(raw_target)
    return not parsed.scheme and not parsed.netloc and not raw_target.startswith("#")


def normalize_target(raw_target: str) -> str:
    target = raw_target.strip()
    target = target.split("?", 1)[0].split("#", 1)[0]
    return unquote(target)


def parse_markdown_target(body: str, start: int) -> tuple[str, int]:
    i = start
    while i < len(body) and body[i].isspace():
        i += 1
    if i >= len(body):
        return "", i
    if body[i] == "<":
        end = body.find(">", i + 1)
        if end == -1:
            return "", i + 1
        return body[i + 1 : end].strip(), end + 1

    target: list[str] = []
    depth = 0
    while i < len(body):
        char = body[i]
        if depth == 0 and (char.isspace() or char == ")"):
            break
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
        target.append(char)
        i += 1
    return "".join(target).strip(), i


def iter_markdown_link_targets(body: str):
    pos = 0
    while True:
        start = body.find("](", pos)
        if start == -1:
            break
        target, end = parse_markdown_target(body, start + 2)
        if target:
            yield start, target
        pos = max(end + 1, start + 2)


def check_target(path: Path, raw_target: str, line_no: int) -> list[str]:
    target = normalize_target(raw_target)
    if not target or not is_local_target(raw_target):
        return []
    target_path = (path.parent / target).resolve()
    try:
        target_path.relative_to(ROOT)
    except ValueError:
        return []
    if target_path.exists():
        return []
    return [
        f"{path.relative_to(ROOT)}:{line_no}: missing local link target: {raw_target}"
    ]


def check_links(path: Path, text: str) -> list[str]:
    issues: list[str] = []
    body = strip_fenced_blocks(text)
    for start, raw_target in iter_markdown_link_targets(body):
        line_no = body[:start].count("\n") + 1
        issues.extend(check_target(path, raw_target, line_no))
    for match in HTML_TARGET_RE.finditer(body):
        raw_target = next(group for group in match.groups() if group is not None).strip()
        line_no = body[: match.start()].count("\n") + 1
        issues.extend(check_target(path, raw_target, line_no))
    return issues


def check_summary_links() -> list[str]:
    summary = ROOT / "SUMMARY.md"
    if not summary.exists():
        return []
    return check_links(summary, summary.read_text(encoding="utf-8", errors="ignore"))


def main() -> int:
    issues: list[str] = []
    files = iter_markdown_files()
    for path in files:
        text = path.read_text(encoding="utf-8", errors="ignore")
        issues.extend(check_fences(path, text))
        issues.extend(check_links(path, text))
    issues.extend(check_summary_links())
    issues.extend(check_volatile_facts())

    unique_issues = sorted(set(issues))
    if unique_issues:
        print("\n".join(unique_issues))
        print(f"\n{len(unique_issues)} issue(s) found across {len(files)} Markdown files.")
        return 1
    print(f"All {len(files)} Markdown files passed project checks.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
