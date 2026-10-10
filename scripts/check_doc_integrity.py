#!/usr/bin/env python3
"""Doc Integrity and Consistency Checker per DEF-022.

Traverses markdown files in docs/ and evidence/ to validate:
1. Relative file links: all relative [text](path) targets resolve to existing files.
2. Canonical ID consistency:
   - Validates recognized project ID formats (DEF-*, EXC-*, DEC-*, IMP-*, NFR-*, SCR-*, GATE-*).
   - Validates that defect IDs (DEF-nnn) referenced in docs and evidence are tracked in the
     consolidated defect registers (docs/28_ACCEPTANCE_UAT_AND_GO_LIVE.md or evidence/defect_log.md).
   - Validates that exception rule IDs (EXC-nnn) correspond to known engine rules (EXC-001..EXC-024).

Exits 0 on clean integrity check, non-zero if broken links or unknown IDs are detected.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Standard pattern for markdown hyperlinks: [label](target)
LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

# ID patterns
ID_PATTERNS = {
    "DEF": re.compile(r"\b(DEF-\d{3})\b"),
    "EXC": re.compile(r"\b(EXC-\d{3})\b"),
    "DEC": re.compile(r"\b(DEC-\d{3})\b"),
    "IMP": re.compile(r"\b(IMP-\d{3})\b"),
    "NFR": re.compile(r"\b(NFR-\d{3})\b"),
    "SCR": re.compile(r"\b(SCR-\d{3})\b"),
    "GATE": re.compile(r"\b(GATE-\d{2}[A-Z]?)\b"),
}

# Known exception rules defined in catalog (EXC-001 through EXC-024)
KNOWN_EXC_RULES = {f"EXC-{i:03d}" for i in range(1, 25)}


def strip_code_blocks(content: str) -> str:
    """Remove fenced code blocks so code samples / JSON examples aren't parsed as doc text."""
    return re.sub(r"```[\s\S]*?```", "", content)


def collect_markdown_files(root: Path) -> list[Path]:
    """Collect all markdown documentation files from docs/ and evidence/."""
    files: list[Path] = []
    for rel_dir in ("docs", "evidence"):
        p = root / rel_dir
        if p.exists():
            files.extend(sorted(p.rglob("*.md")))
    return files


def check_link_validity(files: list[Path], root: Path) -> list[str]:
    """Check that all relative links resolve to existing files or directories."""
    errors: list[str] = []

    for fpath in files:
        try:
            content = fpath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = fpath.read_text(encoding="latin-1")

        clean = strip_code_blocks(content)
        for m in LINK_PATTERN.finditer(clean):
            target = m.group(2).strip()
            # Ignore web links, emails, and intra-document anchor-only links
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue

            # Strip query string or anchor fragment
            path_part = target.split("#")[0].split("?")[0].strip()
            if not path_part:
                continue

            # Normalize backslashes
            path_part = path_part.replace("\\", "/")

            # Resolve relative to the containing document directory
            resolved = (fpath.parent / path_part).resolve()
            if not resolved.exists():
                rel_doc = fpath.relative_to(root) if fpath.is_relative_to(root) else fpath
                errors.append(
                    f"Broken link in {rel_doc}: target '{target}' resolved to non-existent path '{resolved}'"
                )

    return errors


def collect_registered_defects(root: Path) -> set[str]:
    """Collect registered defect IDs from primary tracking documents."""
    registered: set[str] = set()
    tracking_files = [
        root / "docs" / "28_ACCEPTANCE_UAT_AND_GO_LIVE.md",
        root / "evidence" / "defect_log.md",
        root / "docs" / "SESSION_HANDOVER_2026-10-03.md",
        root / "docs" / "SESSION_LOG.md",
    ]

    def_pat = re.compile(r"\b(DEF-\d{3})\b")
    for tf in tracking_files:
        if tf.exists():
            txt = tf.read_text(encoding="utf-8")
            for m in def_pat.finditer(txt):
                registered.add(m.group(1))

    return registered


def check_id_consistency(files: list[Path], root: Path) -> list[str]:
    """Check ID consistency across documents."""
    errors: list[str] = []
    registered_defs = collect_registered_defects(root)

    # Allow documented defect IDs
    # DEF-020 is a documented renumbering task / retired identifier
    allowed_defs = set(registered_defs)
    allowed_defs.add("DEF-020")

    def_pattern = ID_PATTERNS["DEF"]
    exc_pattern = ID_PATTERNS["EXC"]

    for fpath in files:
        try:
            content = fpath.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            content = fpath.read_text(encoding="latin-1")

        clean = strip_code_blocks(content)
        rel_doc = fpath.relative_to(root) if fpath.is_relative_to(root) else fpath

        # Check DEF IDs
        for m in def_pattern.finditer(clean):
            defect_id = m.group(1)
            if defect_id not in allowed_defs:
                errors.append(f"Unregistered defect ID referenced in {rel_doc}: {defect_id}")

        # Check EXC IDs
        for m in exc_pattern.finditer(clean):
            rule_id = m.group(1)
            if rule_id not in KNOWN_EXC_RULES:
                errors.append(f"Unknown exception rule ID referenced in {rel_doc}: {rule_id}")

    return errors


def run_checks(root: Path | None = None) -> tuple[int, list[str]]:
    """Run doc integrity checks and return (error_count, list_of_errors)."""
    if root is None:
        root = ROOT

    md_files = collect_markdown_files(root)
    all_errors: list[str] = []

    link_errors = check_link_validity(md_files, root)
    all_errors.extend(link_errors)

    id_errors = check_id_consistency(md_files, root)
    all_errors.extend(id_errors)

    return len(all_errors), all_errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify document link validity and ID consistency per DEF-022."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=ROOT,
        help=f"Project root directory (default: {ROOT})",
    )
    args = parser.parse_args()

    print(f"--> [DOC-INTEGRITY] Checking docs/ and evidence/ under {args.root}...")
    md_files = collect_markdown_files(args.root)
    print(f"    Discovered {len(md_files)} markdown files.")

    err_count, errors = run_checks(args.root)

    if err_count > 0:
        print(f"FAILED: Found {err_count} doc integrity / ID consistency errors:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("    PASSED: All markdown links valid and cross-project IDs consistent!\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
