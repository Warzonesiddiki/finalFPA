"""Addon 6 (v2) §11 machine gate — reuse/license rails enforced in CI.

Six checks (the five specified in `project prompt/ADDON_6_REUSE.md` §11:
  CHECK 1 — Provenance completeness ("Adapted from" → docs/32 §1 AND THIRD_PARTY_NOTICES.md)
  CHECK 2 — Forbidden licenses in shipped code (app/, ui/, packaging/)
  CHECK 3 — Upstream hygiene (vendor/_upstream gitignored and untracked)
  CHECK 4 — Dependency split (runtime deps on the 4A GO list; DT-* dev-only)
  CHECK 5 — Header format (every "Adapted from" line parses)
  CHECK 6 — Adopted-source notices reach the payload (doc 15 step 4a; added 2026-10-05)

Exit code 0 = all checks pass; 1 = at least one violation (every violation printed).
Authorized by Addon 6 v2 §11; wired into scripts/check.py as its final step.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROVENANCE = ROOT / "docs" / "32_REUSE_AND_PROVENANCE.md"
NOTICES = ROOT / "THIRD_PARTY_NOTICES.md"
SHIP_DIRS = ("app", "ui", "packaging")

# Never descend into these (node_modules ships thousands of third-party license
# strings that are not OUR shipped code; caches are not source).
EXCLUDE_DIRS = {
    "node_modules",
    "__pycache__",
    ".git",
    "dist",
    "build",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".vite",
    "coverage",
    "htmlcov",
    "out",
}
SCAN_SUFFIXES = {
    ".py",
    ".pyi",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".mjs",
    ".cjs",
    ".json",
    ".css",
    ".html",
    ".htm",
    ".md",
    ".yml",
    ".yaml",
    ".toml",
    ".cfg",
    ".ini",
    ".spec",
    ".iss",
    ".bat",
    ".ps1",
    ".sh",
    ".txt",
}

FORBIDDEN_PATTERNS = [
    (re.compile(r"\bAGPL\b", re.IGNORECASE), "AGPL"),
    (re.compile(r"\bGPL\b", re.IGNORECASE), "GPL"),
    (re.compile(r"\bLGPL\b", re.IGNORECASE), "LGPL"),
    (re.compile(r"\bSSPL\b", re.IGNORECASE), "SSPL"),
    (re.compile(r"\bBUSL\b", re.IGNORECASE), "BUSL"),
    (re.compile(r"source-available", re.IGNORECASE), "source-available"),
]

# §11 CHECK 2 exception: notices files "may cite them as refusals". The spec names
# THIRD_PARTY_NOTICES.md (root, outside the scan set — so as written the exception
# could never fire); packaging/THIRD_PARTY_LICENSES.txt is the same artifact under the
# Addon 1 §I name that ships in the installer payload. Interpretation logged as a Tier-B
# note inside DEC-062 (2026-10-05); both filenames are excluded here by role, not content.
NOTICE_EXCEPTION_FILES = {"THIRD_PARTY_NOTICES.md", "THIRD_PARTY_LICENSES.txt"}

# 4A GO list as applied to RUNTIME dependencies (4B: same list minus CC0/BY).
RUNTIME_GO = re.compile(
    r"\b(MIT|Apache(\s|-)?2?\.?0?|Apache Software License|BSD(-\d|-Clause)?|ISC|"
    r"Unlicense|Python Software Foundation License|PSF)\b|"
    # Full-license-text fields (e.g. polars ships the entire MIT text in `License`).
    r"Permission is hereby granted, free of charge|"
    r"Redistribution and use in source and binary forms|"
    r"Apache License, Version 2\.0",
    re.IGNORECASE,
)
RUNTIME_NOT_GO = re.compile(
    r"\b(GPL|AGPL|LGPL|SSPL|BUSL|MPL|CC0|CC-BY|source-available)\b",
    re.IGNORECASE,
)
DT_TOOLS = ("pip-licenses", "faker", "hypothesis")
ADP_RE = re.compile(r"ADP-\d{3}")
# E8: Adapted from <url-ish> @ <7-40 hex> (<license>) — ADP-nnn — …
HEADER_RE = re.compile(r"Adapted from \S+ @ [0-9a-f]{7,40} \([^)]+\) — ADP-\d{3} —")


def iter_shipped_files():
    for base in SHIP_DIRS:
        root = ROOT / base
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
                continue
            if any(part in EXCLUDE_DIRS for part in path.parts):
                continue
            # The notices file may cite forbidden names as refusals (spec exception).
            if path.name in NOTICE_EXCEPTION_FILES:
                continue
            yield path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_1_provenance(violations: list[str]) -> int:
    """Every "Adapted from" file's ADP id must be in docs/32 §1 AND notices."""
    prov_text = read_text(PROVENANCE) if PROVENANCE.exists() else ""
    notices_text = read_text(NOTICES) if NOTICES.exists() else ""
    m = re.search(r"## 1\..*?(?=\n## 2\.)", prov_text, re.DOTALL)
    section_1 = m.group(0) if m else prov_text
    seen = 0
    for path in iter_shipped_files():
        text = read_text(path)
        if "Adapted from" not in text:
            continue
        seen += 1
        for adp in sorted(set(ADP_RE.findall(text))):
            if adp not in section_1:
                violations.append(
                    f"CHECK 1: {path.relative_to(ROOT)} cites {adp}, which is absent from "
                    f"docs/32_REUSE_AND_PROVENANCE.md §1"
                )
            if adp not in notices_text:
                violations.append(
                    f"CHECK 1: {path.relative_to(ROOT)} cites {adp}, which is absent from "
                    f"THIRD_PARTY_NOTICES.md"
                )
    if not PROVENANCE.exists():
        violations.append("CHECK 1: docs/32_REUSE_AND_PROVENANCE.md is missing")
    if not NOTICES.exists():
        violations.append("CHECK 1: THIRD_PARTY_NOTICES.md is missing")
    print(f"  files carrying an 'Adapted from' header: {seen}")
    return seen


def check_2_forbidden_licenses(violations: list[str]) -> int:
    hits = 0
    for path in iter_shipped_files():
        text = read_text(path)
        for pattern, name in FORBIDDEN_PATTERNS:
            for i, line in enumerate(text.splitlines(), 1):
                if pattern.search(line):
                    hits += 1
                    violations.append(
                        f"CHECK 2: forbidden license name '{name}' at "
                        f"{path.relative_to(ROOT)}:{i}: {line.strip()[:120]}"
                    )
    print(f"  forbidden-license hits in shipped code: {hits}")
    return hits


def check_3_upstream_hygiene(violations: list[str]) -> None:
    gitignore = read_text(ROOT / ".gitignore")
    if "vendor/_upstream" not in gitignore:
        violations.append("CHECK 3: 'vendor/_upstream/' is not listed in .gitignore")
    try:
        res = subprocess.run(
            ["git", "ls-files", "vendor/_upstream"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        tracked = [ln for ln in res.stdout.splitlines() if ln.strip()]
        if res.returncode != 0:
            violations.append(f"CHECK 3: git ls-files failed: {res.stderr.strip()[:200]}")
        for ln in tracked:
            violations.append(f"CHECK 3: upstream file tracked in git: {ln}")
        print(
            f"  gitignored: {'vendor/_upstream/' in gitignore}; tracked upstream files: {len(tracked)}"
        )
    except OSError as exc:
        violations.append(f"CHECK 3: could not run git: {exc}")


def _requirement_name(spec: str) -> str:
    return re.split(r"[\s\[<>=!~;()]", spec.strip(), maxsplit=1)[0]


def _license_of(name: str) -> str:
    """License blob for a distribution: expression + classifiers + License field.

    Some packages (polars) put the ENTIRE license text in `License` instead of a
    short id, so the classifier and the full text are both consulted before the
    GO/no-GO decision (detection fix, Tier-B logged in DEC-062).
    """
    try:
        from importlib import metadata
    except ImportError:  # pragma: no cover
        return ""
    try:
        meta = metadata.metadata(name)
    except metadata.PackageNotFoundError:
        return ""
    parts = []
    expression = (meta.get("License-Expression") or "").strip()
    if expression and expression.upper() != "UNKNOWN":
        parts.append(expression)
    for classifier in meta.get_all("Classifier") or []:
        if classifier.startswith("License :: "):
            parts.append(classifier.split(" :: ", 2)[-1])
    license_field = (meta.get("License") or "").strip()
    if license_field and license_field.upper() != "UNKNOWN":
        parts.append(license_field)
    return " | ".join(parts)


def check_4_dependency_split(violations: list[str]) -> None:
    pyproject = ROOT / "pyproject.toml"
    if not pyproject.exists():
        violations.append("CHECK 4: pyproject.toml is missing")
        return
    data = tomllib.loads(read_text(pyproject))
    project = data.get("project", {})
    runtime = list(project.get("dependencies", []) or [])
    dev = []
    for extra in (project.get("optional-dependencies") or {}).values():
        dev.extend(extra)
    runtime_names = {_requirement_name(s).lower() for s in runtime}
    dev_names = {_requirement_name(s).lower() for s in dev}

    unknown = 0
    for spec in runtime:
        name = _requirement_name(spec)
        license_text = _license_of(name)
        if not license_text:
            unknown += 1
            print(f"  WARNING (CHECK 4): license metadata not found for runtime dep '{name}'")
            continue
        if RUNTIME_NOT_GO.search(license_text):
            violations.append(
                f"CHECK 4: runtime dependency '{name}' has a non-GO license: {license_text}"
            )
        elif not RUNTIME_GO.search(license_text):
            violations.append(
                f"CHECK 4: runtime dependency '{name}' license not on the 4A GO list: {license_text}"
            )

    for dt in DT_TOOLS:
        if dt in runtime_names:
            violations.append(
                f"CHECK 4: dev-only tool '{dt}' appears in RUNTIME dependencies (4B violation)"
            )
        where = "dev extras" if dt in dev_names else "absent"
        print(f"  DT tool '{dt}': {where}")

    print(
        f"  runtime deps checked: {len(runtime)} (GO-list), dev extras: {len(dev)}; "
        f"license metadata unavailable: {unknown}"
    )


def check_5_header_format(violations: list[str]) -> int:
    lines_seen = 0
    for path in iter_shipped_files():
        for i, line in enumerate(read_text(path).splitlines(), 1):
            if "Adapted from" not in line:
                continue
            lines_seen += 1
            if not HEADER_RE.search(line):
                violations.append(
                    f"CHECK 5: malformed header at {path.relative_to(ROOT)}:{i}: "
                    f"{line.strip()[:120]}"
                )
    print(f"  'Adapted from' lines examined: {lines_seen}")
    return lines_seen


def check_6_payload_notices(violations: list[str], root: Path = ROOT) -> int:
    """Doc 15 step 4a: the payload notices file must carry every adopted-source
    notice, because copied source is not a distribution dependency and no SBOM lists it.

    Runs the real generator (`build.build_licence_text`) rather than reading a checked-in
    copy, so the check tests what actually ships."""
    sys.path.insert(0, str(root / "scripts"))
    try:
        import build as build_mod
    except Exception as exc:
        violations.append(f"CHECK 6: could not import scripts/build.py: {exc}")
        return 1
    with tempfile.TemporaryDirectory() as td:
        text = build_mod.build_licence_text(root, Path(td))
    cited = set()
    for path in sorted(SHIP_DIRS and [root / d for d in SHIP_DIRS]):
        if not path.is_dir():
            continue
        for f in path.rglob("*"):
            if f.is_file() and f.suffix in {".py", ".ts", ".tsx", ".js", ".md", ".txt"}:
                try:
                    body = f.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                if "Adapted from" in body:
                    cited |= set(re.findall(r"ADP-\d{3}", body))
    missing = sorted(a for a in cited if a not in text)
    if missing:
        violations.append(
            "CHECK 6: adopted source(s) "
            + ", ".join(missing)
            + " ship code in the binary but their notice is absent from the generated payload THIRD_PARTY_LICENSES.txt (doc 15 step 4a)"
        )
    return 1 if missing else 0


def main() -> int:
    # D-20: Windows cp1252 consoles cannot encode box-drawing/✗; keep UTF-8 output pure.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):  # pragma: no cover
            pass
    print("=== Addon 6 v2 §11 — License & Provenance Gate ===")
    violations: list[str] = []

    print("CHECK 1 — Provenance completeness")
    check_1_provenance(violations)

    print("CHECK 2 — Forbidden licenses in shipped code")
    check_2_forbidden_licenses(violations)

    print("CHECK 3 — Upstream hygiene")
    check_3_upstream_hygiene(violations)

    print("CHECK 4 — Dependency split")
    check_4_dependency_split(violations)

    print("CHECK 5 — Header format")
    check_5_header_format(violations)

    print("CHECK 6 — Adopted-source notices reach the payload (doc 15 step 4a)")
    check_6_payload_notices(violations)

    if violations:
        print(f"\nVIOLATIONS: {len(violations)}")
        for v in violations:
            print(f"  ✗ {v}")
        return 1
    print("\nPASSED: all six checks clean (Addon 6 v2 §11 + doc 15 step 4a).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
