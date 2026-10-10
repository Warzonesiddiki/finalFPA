"""Build pipeline per 15_PACKAGING_DEPLOYMENT_RUNBOOK.md.

Implements all ten steps of doc 15 section 3.2 plus the five preconditions of
section 3.1. Spec text quoted at each step below is verbatim from doc 15.

Design rules taken from the runbook:

* "Excludes are auditable, not folklore" (section 3.4) - the audit fails if
  `pyinstaller.spec` has an exclude without a comment naming what pulled it in.
* "a version string is never typed twice" (section 2.2) - the version is read
  from `pyproject.toml` and cross-checked against `app/__init__.py`; it is never
  typed here.
* "the compiler path is discovered, never hard-coded per machine" (section 2.1)
  - Inno Setup and git are discovered on PATH, not absolute-pathed.
* `packaging/out/` is the only output location for artefacts (section 2.3).

Two honesty rules this script deliberately enforces on itself:

1. A missing required asset is reported as a BLOCKER and fails the audit. The
   script never fabricates a placeholder icon, template, or licence file to make
   the payload look complete - an audit that passes on invented content is worse
   than no audit.
2. NFR-006 is measured on the Inno Setup artefact (doc 14 line 84). If Inno
   Setup is absent, the report says NFR-006 is NOT VERIFIED and shows the
   portable zip size clearly labelled as a proxy. It never reports a proxy as a
   pass.

Usage:
    python scripts/build.py [--dev] [--skip-installer] [--skip-check] [--no-smoke]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

# --------------------------------------------------------------------------
# Frozen constants owned by doc 15. Artefact names from section 1.2 / 10.
# --------------------------------------------------------------------------
APP_NAME = "FPandAMonthEndCopilot"
DISPLAY_NAME = "FP&A Month-End Copilot"
PUBLISHER = "FP&A Solutions"
INSTALLER_STEM = f"Setup-{APP_NAME}"
NFR_006_MAX_BYTES = 500 * 1024 * 1024  # doc 15 section 3.3 / doc 14 NFR-006

#: Files that must sit beside the exe for the payload to be complete.
#: Doc 15 section 3.2 step 4 and step 5.
REQUIRED_PAYLOAD_ENTRIES: tuple[str, ...] = (
    "README.txt",
    "THIRD_PARTY_LICENSES.txt",
    "templates",
)

#: Names that must never appear in the payload. Doc 15 sections 1.2 and 3.2
#: step 5 ("no tests/, no docs/, no sample-data/generator, no .env").
FORBIDDEN_PAYLOAD_NAMES: tuple[str, ...] = (
    "tests",
    "test",
    "docs",
    "sample-data",
    ".env",
    "__pycache__",
    "generate_sample_data.py",
)

#: Key material that must never ship. Doc 15 section 3.2 step 5, SEC-031.
#: NOTE: `.pem` is NOT blanket-forbidden because `certifi/cacert.pem` is a CA
#: bundle, not a secret. Only *key* extensions are forbidden.
FORBIDDEN_SUFFIXES: tuple[str, ...] = (
    ".pfx",
    ".p12",
    ".key",
    ".pem-key",
    ".keystore",
    ".jks",
)

#: Source assets that must exist before a build (doc 15 section 3.1 #4 and 2.3).
REQUIRED_SOURCE_ASSETS: tuple[str, ...] = (
    "packaging/icons/app.ico",
    "packaging/installer.iss",
    "packaging/pyinstaller.spec",
    "ui/package.json",
    "ui/package-lock.json",
    "pyproject.toml",
)

#: The deck + input workbook templates named in doc 15 section 2.3.
REQUIRED_TEMPLATES: tuple[str, ...] = ("FPAMonthEndCopilot_v1.pptx",)

#: Layout names doc 12 section 3.6 requires in the deck template.
REQUIRED_PPTX_LAYOUTS: tuple[str, ...] = (
    "FPA-PPT-001",
    "FPA-PPT-002",
    "FPA-PPT-003",
    "FPA-PPT-004",
    "FPA-PPT-005",
    "FPA-PPT-006",
    "FPA-PPT-DISCLAIMER",
)

#: Smallest plausible ICO/pptx. A real .ico is >= 1 KB; a real .pptx is a ZIP
#: holding OOXML parts, comfortably > 10 KB. Anything under these is a stub.
MIN_ICO_BYTES = 1024
MIN_PPTX_BYTES = 10_000


def _is_valid_ico(path: Path) -> bool:
    """True only for a real Windows icon: >= MIN_ICO_BYTES and an ICO header.

    An ICO file is a 6-byte header: reserved=0, type=1 (icon), then the image
    count. A text placeholder fails both checks.
    """
    try:
        data = path.read_bytes()
    except OSError:
        return False
    if len(data) < MIN_ICO_BYTES or len(data) < 6:
        return False
    reserved, ico_type = int.from_bytes(data[0:2], "little"), int.from_bytes(data[2:4], "little")
    if reserved != 0 or ico_type != 1:
        return False
    count = int.from_bytes(data[4:6], "little")
    return count > 0


def _validate_pptx_template(path: Path) -> None:
    """Raise BuildError unless path is a real, doc-12-conformant deck template.

    A .pptx is an OOXML ZIP package. We require: a plausible file size, a ZIP
    magic header, and every layout name in REQUIRED_PPTX_LAYOUTS present in
    ppt/slideLayouts/. Named shapes are the author's responsibility per doc 12
    section 3.6, but the layout set is machine-checkable and is what the engine
    resolves against.
    """
    if not path.exists():
        raise BuildError("missing")
    size = path.stat().st_size
    if size < MIN_PPTX_BYTES:
        raise BuildError(
            f"not a real .pptx - {size} bytes is below the {MIN_PPTX_BYTES}-byte "
            f"floor for an OOXML package (placeholder file?)"
        )
    with zipfile.ZipFile(path) as zf:
        if zf.testzip() is not None:
            raise BuildError("corrupt ZIP container")
        # Read the parts straight off the archive handle: passing a bare member
        # name to Path() would look on disk instead of inside the ZIP.
        blob = "\n".join(
            zf.read(n).decode("utf-8", errors="ignore")
            for n in zf.namelist()
            if n.startswith("ppt/slideLayouts/") and n.endswith(".xml")
        )
        absent = [n for n in REQUIRED_PPTX_LAYOUTS if n not in blob]
        if absent:
            raise BuildError(
                "doc 12 section 3.6 requires layouts "
                + ", ".join(REQUIRED_PPTX_LAYOUTS)
                + "; missing "
                + ", ".join(absent)
            )


# --------------------------------------------------------------------------
# Stage bookkeeping
# --------------------------------------------------------------------------


@dataclass
class StageResult:
    number: int
    name: str
    status: str = "pending"  # pass | fail | skip
    seconds: float = 0.0
    detail: str = ""
    errors: list[str] = field(default_factory=list)
    blockers: list[str] = field(default_factory=list)

    def render(self) -> str:
        mark = {"pass": "PASS", "fail": "FAIL", "skip": "SKIP"}.get(self.status, "?")
        line = f"  [{mark}] step {self.number:>2} {self.name} ({self.seconds:.1f}s)"
        if self.detail:
            line += f" - {self.detail}"
        for b in self.blockers:
            line += f"\n         BLOCKER: {b}"
        for e in self.errors:
            line += f"\n         ERROR:   {e}"
        return line


class BuildReport:
    """Collects every stage result so the run always produces one transcript."""

    def __init__(self) -> None:
        self.stages: list[StageResult] = []
        self.started = time.perf_counter()

    def add(self, stage: StageResult) -> StageResult:
        self.stages.append(stage)
        return stage

    @property
    def failed(self) -> bool:
        return any(s.status == "fail" for s in self.stages)

    def render(self) -> str:
        head = "FP&A Month-End Copilot - build report"
        lines = [head, "=" * len(head)]
        lines += [s.render() for s in self.stages]
        total = time.perf_counter() - self.started
        lines.append(f"  total build duration: {total:.1f}s")
        return "\n".join(lines)


class BuildError(RuntimeError):
    """Fatal precondition failure carrying doc 15's own failure message."""


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------


def log(msg: str) -> None:
    print(f"--> [BUILD] {msg}", flush=True)


def run(cmd: Sequence[str], desc: str, cwd: Path | None = None) -> subprocess.CompletedProcess:
    """Run a command, streaming its output. Never shell=True for list commands."""
    printable = " ".join(str(c) for c in cmd)
    log(f"{desc}: {printable}")
    return subprocess.run(
        [str(c) for c in cmd],
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
    )


def which(name: str) -> Path | None:
    """Discover a tool on PATH.

    Doc 15 section 2.1: "the compiler path is discovered, never hard-coded per
    machine."
    """
    found = shutil.which(name)
    return Path(found) if found else None


def dir_size(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def human(n: int) -> str:
    return f"{n / (1024 * 1024):.1f} MB"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_version(root: Path) -> str:
    """Read the single version source (doc 15 section 2.2)."""
    text = (root / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    if not m:
        raise BuildError("Version '<unreadable>' is not semver.")
    return m.group(1)


SEMVER = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


# --------------------------------------------------------------------------
# Section 3.1 - Preconditions (fail fast, in this order)
# --------------------------------------------------------------------------


def preconditions(root: Path, args: argparse.Namespace, version: str) -> None:
    """Doc 15 section 3.1, checked in the documented order.

    | # | Check | Failure message |
    | 1 | Clean working tree (unless --dev) | "The repository has uncommitted
          changes - commit or use --dev." |
    | 2 | scripts/check green (full form)   | transcript printed, build stops |
    | 3 | Version resolvable and semver-valid | "Version '<x>' is not semver." |
    | 4 | Required assets present           | names the missing asset |
    | 5 | Inno Setup compiler found         | "Inno Setup not found - install
          it or pass --skip-installer." |
    """

    # --- 1. Clean working tree -------------------------------------------------
    git = which("git")
    if git is None:
        # Not a hard failure: the tool is absent, so the check is UNEVALUABLE and
        # saying "pass" would be a lie. Reported as skipped, not passed.
        log("precondition 1 (clean tree): SKIPPED - git is not on PATH, cannot evaluate")
    elif (root / ".git").exists():
        if args.dev:
            log("precondition 1 (clean tree): waived by --dev")
        else:
            res = run([git, "-C", root, "status", "--porcelain"], "check working tree")
            if res.returncode == 0 and res.stdout.strip():
                raise BuildError("The repository has uncommitted changes - commit or use --dev.")
            log("precondition 1 (clean tree): pass")
    else:
        log("precondition 1 (clean tree): SKIPPED - not a git checkout")

    # --- 2. scripts/check green ------------------------------------------------
    check_script = root / "scripts" / "check.py"
    if args.skip_check:
        log("precondition 2 (scripts/check): waived by --skip-check")
    elif not check_script.exists():
        raise BuildError(f"scripts/check is missing: {check_script}")
    else:
        log("precondition 2 (scripts/check): running the full form")
        res = run([sys.executable, str(check_script)], "scripts/check", cwd=root)
        print(res.stdout[-4000:])
        if res.returncode != 0:
            print(res.stderr[-4000:])
            raise BuildError("scripts/check is not green; the build stops.")

    # --- 3. Version resolvable and semver-valid -------------------------------
    if not SEMVER.match(version):
        raise BuildError(f"Version '{version}' is not semver.")
    # Section 2.2: "a version string is never typed twice".
    init_text = (root / "app" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'__version__\s*=\s*"([^"]+)"', init_text)
    if m and m.group(1) != version:
        raise BuildError(
            f"Version '{version}' is not semver / does not match app/__init__.py "
            f"'{m.group(1)}' (doc 15 section 2.2: a version is never typed twice)."
        )
    log(f"precondition 3 (semver): pass - {version}")

    # --- 4. Required assets present -------------------------------------------
    missing = [p for p in REQUIRED_SOURCE_ASSETS if not (root / p).exists()]
    tpl_dir = root / "packaging" / "templates"
    missing_templates = []
    if not tpl_dir.is_dir():
        missing.append("packaging/templates/")
    else:
        present = {p.name for p in tpl_dir.iterdir()}
        missing_templates = [t for t in REQUIRED_TEMPLATES if t not in present]
        if missing_templates:
            missing.append("packaging/templates/" + ", ".join(missing_templates))
    if missing:
        for item in missing:
            log(f"MISSING ASSET: {item}")
        raise BuildError("Required build assets are missing: " + "; ".join(missing))

    # --- 4b. Required assets are VALID, not merely present (DEF-011) -----------
    # DEF-011: the gate above passed on filename alone, so 15-byte and 16-byte
    # ASCII placeholder files ("ICO_PLACEHOLDER", "PPTX_PLACEHOLDER") satisfied
    # doc 15 section 3.1 #4 and shipped inside a 76 MB installer. Presence is not
    # asset validation; a real build must refuse a stub.
    invalid: list[str] = []
    ico_path = root / "packaging" / "icons" / "app.ico"
    if not _is_valid_ico(ico_path):
        invalid.append(
            f"packaging/icons/app.ico is not a valid ICO ({ico_path.stat().st_size} bytes)"
        )
    for tpl_name in REQUIRED_TEMPLATES:
        tpl_path = tpl_dir / tpl_name
        try:
            _validate_pptx_template(tpl_path)
        except BuildError as exc:
            invalid.append(f"packaging/templates/{tpl_name}: {exc}")
    if invalid:
        for item in invalid:
            log(f"INVALID ASSET: {item}")
        raise BuildError("Required build assets are present but invalid: " + "; ".join(invalid))
    log("precondition 4b (asset validity): pass")
    log("precondition 4 (required assets): pass")

    # --- 5. Inno Setup compiler found -----------------------------------------
    if args.skip_installer:
        log("precondition 5 (Inno Setup): waived by --skip-installer")
        return
    if find_iscc() is None:
        raise BuildError("Inno Setup not found - install it or pass --skip-installer.")
    log("precondition 5 (Inno Setup): pass")


def find_iscc() -> Path | None:
    """Discover ISCC.exe - discovered, never hard-coded (doc 15 section 2.1)."""
    on_path = which("ISCC")
    if on_path:
        return on_path
    for candidate in (
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(os.path.expandvars(r"%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe")),
    ):
        if candidate.exists():
            return candidate
    return None


# --------------------------------------------------------------------------
# Section 2.2 - Version stamping
# --------------------------------------------------------------------------


def generate_version_info(root: Path, version: str) -> Path:
    """Step: `packaging/version_info.txt` - "Same version + product name +
    company", "Written by: scripts/build" (doc 15 section 2.2)."""
    out = root / "packaging" / "version_info.txt"
    major, minor, patch = (version.split(".") + ["0", "0"])[:3]
    out.write_text(
        "\n".join(
            [
                "# Generated by scripts/build - do not edit by hand (doc 15 section 2.2).",
                "VSVersionInfo(",
                "  ffi=FixedFileInfo(",
                f"    filevers={major}.{minor}.{patch}.0,",
                f"    prodvers={major}.{minor}.{patch}.0,",
                "    flags=0x0,",
                '    OS=0x40004,"',
                '    fileType=0x1,"',
                '    subtype=0x0,"',
                "    date=(0, 0)",
                "  ),",
                "  kids=[",
                "    StringFileInfo(['",
                "      '040904B0',",
                f"      ['CompanyName', '{PUBLISHER}'],",
                f"      ['FileDescription', '{DISPLAY_NAME}'],",
                f"      ['FileVersion', '{version}'],",
                f"      ['InternalName', '{APP_NAME}'],",
                f"      ['LegalCopyright', '{PUBLISHER}'],",
                f"      ['OriginalFilename', '{APP_NAME}.exe'],",
                f"      ['ProductName', '{DISPLAY_NAME}'],",
                f"      ['ProductVersion', '{version}']",
                "    ]",
                "  ]),",
                "  VarFileInfo([",
                "    ['Translation', 0x409, 1200]",
                "  ])",
                ")",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return out


# --------------------------------------------------------------------------
# Step 4 - Payload staging
# --------------------------------------------------------------------------


def stage_payload(root: Path, payload: Path, version: str) -> tuple[list[str], list[str]]:
    """Doc 15 section 3.2 step 4:

    "Stage the payload beside the exe: `templates/` (deck + input `.xlsx`),
    `THIRD_PARTY_LICENSES.txt` (Python **and** UI dependencies), `README.txt`
    (first-run pointer, portable-mode note), the EULA/disclaimer text"
    """
    log("staging payload beside the exe")
    payload.mkdir(parents=True, exist_ok=True)
    staged: list[str] = []
    blockers: list[str] = []

    # templates/ - copied if present, never invented. Presence is validated
    # properly by the step 5 audit; staging only reports what it could copy.
    tpl_src = root / "packaging" / "templates"
    if tpl_src.is_dir() and any(tpl_src.iterdir()):
        shutil.copytree(tpl_src, payload / "templates", dirs_exist_ok=True)
        staged.append("templates/")
    else:
        blockers.append(
            "packaging/templates/ is missing or empty - the deck and input .xlsx "
            "are built assets and are not in the repository. Payload would ship "
            "without them. NOT fabricated by this script."
        )

    # THIRD_PARTY_LICENSES.txt - generated from real metadata in the bundle plus
    # ui/package-lock.json. Derived, never invented.
    licences = payload / "THIRD_PARTY_LICENSES.txt"
    licences.write_text(build_licence_text(root, payload), encoding="utf-8")
    staged.append("THIRD_PARTY_LICENSES.txt")

    # README.txt - first-run pointer + portable-mode note, from doc 15 section 4.3.
    readme = payload / "README.txt"
    readme.write_text(build_readme_text(version), encoding="utf-8")
    staged.append("README.txt")

    # EULA/disclaimer - doc 15 step 4 requires it, but the repository ships no
    # source text for it. Reported as a blocker, never written from thin air.
    eula_src = None
    for name in ("EULA.txt", "DISCLAIMER.txt"):
        if (root / "packaging" / name).exists():
            eula_src = root / "packaging" / name
            break
    if eula_src:
        shutil.copy2(eula_src, payload / eula_src.name)
        staged.append(eula_src.name)
    else:
        blockers.append(
            "EULA/disclaimer text has no source in the repository "
            "(expected packaging/EULA.txt or packaging/DISCLAIMER.txt). "
            "Doc 15 section 3.2 step 4 requires it in the payload. NOT written "
            "by this script - legal text is owned by docs 22/23/29."
        )

    return staged, blockers


def build_licence_text(root: Path, payload: Path) -> str:
    """Assemble THIRD_PARTY_LICENSES.txt from Python AND UI dependencies.

    Doc 15 section 3.2 step 4 requires both. Python licences are taken from the
    `*.dist-info/licenses/` trees inside the bundle that PyInstaller produced -
    the same files actually shipping, not a guess from the local env.
    """
    lines = [
        "THIRD PARTY LICENSES",
        "=" * 60,
        "",
        f"{DISPLAY_NAME} - generated by scripts/build at build time.",
        "",
        "Part 1 - Python dependencies (from the shipped bundle's dist-info)",
        "-" * 60,
    ]
    internal = payload / "_internal"
    py_entries: list[tuple[str, str, str]] = []
    if internal.is_dir():
        for dist in sorted(internal.glob("*.dist-info")):
            name, _, version = dist.name[: -len(".dist-info")].partition("-")
            lic = "see bundled licence files"
            lic_dir = dist / "licenses"
            found = sorted(p for p in lic_dir.rglob("*") if p.is_file()) if lic_dir.is_dir() else []
            if found:
                lic = ", ".join(p.name for p in found[:4])
            py_entries.append((name, version, lic))
    for name, version, lic in py_entries:
        lines.append(f"  {name} {version} - {lic}")
    if not py_entries:
        lines.append("  (no *.dist-info directories found in the payload)")

    lines += ["", "Part 2 - UI dependencies (from ui/package-lock.json)", "-" * 60]
    lock = root / "ui" / "package-lock.json"
    if lock.exists():
        try:
            data = json.loads(lock.read_text(encoding="utf-8"))
            for name, meta in sorted(data.get("packages", {}).items()):
                if not name or not meta.get("version"):
                    continue
                lic = meta.get("license") or "see project repository"
                lines.append(f"  {name} {meta['version']} - {lic}")
        except json.JSONDecodeError as exc:
            lines.append(f"  (could not parse package-lock.json: {exc})")
    else:
        lines.append("  (ui/package-lock.json missing)")

    lines += [
        "",
        "Full licence texts for the Python dependencies are bundled beside this",
        "file in _internal/*.dist-info/licenses/. UI dependency licences are",
        "published with each npm package and listed above by name and version.",
        "",
        "",
        "Part 3 - Adopted source (copy-edit) notices",
        "------------------------------------------------------------",
    ]
    # Doc 15 step 4a: copied source is NOT a distribution dependency, so neither
    # pip freeze nor an SBOM lists it - this file is the only place a user
    # licence obligation is discharged. Derived verbatim from THIRD_PARTY_NOTICES.md
    # and never hand-written here, so the payload cannot drift from the registry.
    lines += _adopted_source_notices(root)
    lines.append("")
    return "\n".join(lines)


def _adopted_source_notices(root: Path) -> list[str]:
    """The `## WS-nn ... (ADP-nnn)` sections of THIRD_PARTY_NOTICES.md, verbatim."""
    notices = root / "THIRD_PARTY_NOTICES.md"
    if not notices.exists():
        return [
            "  (THIRD_PARTY_NOTICES.md is missing - this payload would ship",
            "   copied source with no notice. See docs/15 step 4a.)",
        ]
    out: list[str] = []
    keep = False
    for line in notices.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            keep = bool(re.match(r"##\s+WS-\d+", line))
        if keep:
            out.append(line)
    if not out:
        return ["  (THIRD_PARTY_NOTICES.md lists no adopted sources)"]
    return out


def build_readme_text(version: str) -> str:
    """README.txt - first-run pointer + portable-mode note (doc 15 section 4.3)."""
    return "\n".join(
        [
            f"{DISPLAY_NAME} {version} - portable package",
            "=" * 60,
            "",
            "WHAT THIS IS",
            "",
            "This is the no-install variant of the application, intended for",
            "locked-down machines and demos. Unzip it anywhere you can write and run",
            f"{APP_NAME}.exe.",
            "",
            "WHAT PORTABLE MODE DOES",
            "",
            "  * Installs nothing. No Start-menu entry, no uninstall entry, no",
            "    Windows Installer record.",
            "  * Writes nothing to the registry.",
            "",
            "WHAT PORTABLE MODE DOES NOT DO",
            "",
            '  * "Portable" means "no install", NOT "no trace". By default your data',
            f"    still lives in %LOCALAPPDATA%\\{DISPLAY_NAME}\\ and is NOT stored",
            "    inside this folder.",
            "  * You still need somewhere writable for that data directory.",
            "",
            "OPTIONAL SELF-CONTAINED MODE",
            "",
            "  Create an empty file named portable.flag beside the executable and the",
            "  application will instead keep its data in a data\\ subfolder next to",
            "  itself, travelling with this folder.",
            "",
            "  WARNING: if you enable this, do not put the application in a synced",
            "  or shared folder. The database is a single file, and concurrent sync",
            "  can corrupt it. The application shows a persistent banner when this",
            "  mode is active.",
            "",
            "LIMITATIONS",
            "",
            "  * No Start-menu shortcut and no uninstall entry.",
            "  * Explorer shows no file-version metadata for the executable.",
            "  * The synced-folder warning above applies in self-contained mode.",
            "",
            "FIRST RUN",
            "",
            "  On first launch the application creates its data directory and",
            "  offers the bundled synthetic sample project so you can see a complete",
            "  month-end run before importing anything of your own.",
            "",
            "UPDATING",
            "",
            "  Replace this folder with the new version. The database schema migrates",
            "  forward automatically on first open, taking a mandatory backup first.",
            "  Downgrades are not supported.",
            "",
            "VERIFYING THIS PACKAGE",
            "",
            "  This package ships with a SHA-256 checksum file. Compare it before",
            "  first use - see the delivery notes for the expected value.",
            "",
        ]
    )


# --------------------------------------------------------------------------
# Step 5 - Payload audit
# --------------------------------------------------------------------------


def audit_payload(root: Path, payload: Path) -> tuple[list[str], list[str], dict[str, int]]:
    """Doc 15 section 3.2 step 5:

        "**Payload audit** (automated): required files present; no `tests/`, no
        `docs/`, no `sample-data/generator`, no `.env`, no `.py` sources of client
        code beyond what PyInstaller needs, no key material (`SEC-031`)"

    Doc 15 section 3.4 adds: the audit "fails on a module that reappears through
    a hidden import", and the spec's excludes must each carry a pull-reason
    comment.
    """
    log("auditing payload")
    errors: list[str] = []
    blockers: list[str] = []

    if not payload.is_dir():
        return ([f"payload directory does not exist: {payload}"], [], {})

    # -- required files present (step 5, first clause) -------------------------
    for entry in REQUIRED_PAYLOAD_ENTRIES:
        if not (payload / entry).exists():
            errors.append(f"required payload entry missing: {entry}")

    # -- templates/ must contain the real built assets -------------------------
    # A presence-only check is not enough: a zero-byte deck satisfies
    # `exists()` and would ship a payload that cannot generate a pack. The
    # runbook calls these "built assets" (section 2.3), so each one must be
    # present AND non-empty.
    tpl_dir = payload / "templates"
    if tpl_dir.is_dir():
        for name in REQUIRED_TEMPLATES:
            tpl = tpl_dir / name
            if not tpl.exists():
                errors.append(f"required template missing from payload: templates/{name}")
            elif tpl.stat().st_size == 0:
                errors.append(
                    f"template templates/{name} is 0 bytes - present but not a "
                    "usable built asset (doc 15 section 2.3)"
                )
    else:
        for name in REQUIRED_TEMPLATES:
            errors.append(
                f"required template missing from payload: templates/{name} "
                "(templates/ directory is absent)"
            )

    # -- forbidden directories / files (step 5, second clause) -----------------
    for path in payload.rglob("*"):
        if path.name in FORBIDDEN_PAYLOAD_NAMES:
            errors.append(f"forbidden payload entry present: {path.relative_to(payload)}")

    # -- no .py sources of client code beyond what PyInstaller needs ----------
    py_sources = [p for p in payload.rglob("*.py") if "__pycache__" not in p.parts]
    if py_sources:
        rel = ", ".join(str(p.relative_to(payload)) for p in py_sources[:5])
        errors.append(f"{len(py_sources)} .py source file(s) in payload: {rel}")

    # -- no key material (SEC-031) ---------------------------------------------
    for path in payload.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() in FORBIDDEN_SUFFIXES:
            errors.append(f"key material in payload: {path.relative_to(payload)}")

    # -- pyinstaller.spec sanity check -----------------------------------------
    spec_path = root / "packaging" / "pyinstaller.spec"
    if not spec_path.is_file():
        blockers.append("pyinstaller.spec missing from packaging/ (doc 15 section 3.2)")
    elif spec_path.stat().st_size == 0:
        blockers.append("pyinstaller.spec is empty in packaging/ (doc 15 section 3.2)")
    else:
        spec_excludes = parse_spec_excludes(root)
        if not spec_excludes:
            blockers.append(
                "pyinstaller.spec defines no excludes list or failed to parse (doc 15 section 3.4)"
            )
        else:
            for name in spec_excludes:
                if not exclude_has_comment(root, name):
                    errors.append(
                        f"pyinstaller.spec excludes '{name}' with no comment naming what "
                        "pulled it in - doc 15 section 3.4: 'An unexplained exclude is a "
                        "review failure'."
                    )

    # -- payload size breakdown for step 10 ------------------------------------
    breakdown: dict[str, int] = {}
    for child in sorted(payload.iterdir()):
        if child.is_dir():
            breakdown[child.name] = dir_size(child)
        else:
            breakdown[child.name] = child.stat().st_size

    if blockers:
        errors.extend(blockers)
    return errors, blockers, breakdown


def parse_spec_excludes(root: Path) -> list[str]:
    """Read the `excludes = [...]` list out of packaging/pyinstaller.spec.

    Comments are stripped BEFORE the module names are extracted. Without that,
    an apostrophe inside a pull-reason comment (for example "application's" or
    "pywebview's") is read as a string delimiter and the parser emits garbage
    entries, which would make the audit fail for the wrong reason.
    """
    spec = root / "packaging" / "pyinstaller.spec"
    if not spec.exists():
        return []
    text = spec.read_text(encoding="utf-8")
    m = re.search(r"^excludes\s*=\s*\[(.*?)\]", text, re.MULTILINE | re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    # Drop `# ...` to end of line. The excludes block contains no string
    # literals with a '#' in them, so line-wise stripping is safe here.
    block = "\n".join(line.split("#", 1)[0] for line in block.splitlines())
    return re.findall(r"['\"]([^'\"]+)['\"]", block)


def exclude_has_comment(root: Path, module: str) -> bool:
    """True when the spec has a comment naming this module as the pulled-in cause.

    Doc 15 section 3.4: the excludes list "carries a comment per entry naming
    what pulled the module in and why it is safe to drop."
    """
    spec = root / "packaging" / "pyinstaller.spec"
    if not spec.exists():
        return False
    for line in spec.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") and module.split(".")[0] in stripped:
            return True
    return False


# --------------------------------------------------------------------------
# Step 7 - Portable zip
# --------------------------------------------------------------------------


def build_portable_zip(root: Path, payload: Path, out_dir: Path, version: str) -> Path | None:
    """Doc 15 section 3.2 step 7:

    "Build the portable zip from the same payload directory (with
    `portable.flag` documentation inside)"
    """
    log("building portable zip")
    out_dir.mkdir(parents=True, exist_ok=True)
    zip_path = out_dir / f"{APP_NAME}-{version}-portable.zip"

    # The flag file documents itself inside the archive (step 7) rather than
    # enabling self-contained mode by default - doc 15 section 4.3 makes it
    # opt-in.
    flag_doc = payload / "portable.flag.README.txt"
    flag_doc.write_text(
        "\n".join(
            [
                "portable.flag - opt-in self-contained data mode (ADR-004)",
                "=" * 60,
                "",
                "This directory intentionally contains a DOCUMENTATION file named",
                "portable.flag.README.txt, not a live portable.flag.",
                "",
                "To enable self-contained mode, create an EMPTY file named exactly",
                f"'portable.flag' beside {APP_NAME}.exe. The application then keeps",
                "its data in a data\\ subfolder that travels with this folder.",
                "",
                "Why the flag is not shipped live: enabling it by default would move",
                "the database next to the executable, so every copy, backup and sync",
                "would duplicate it. See doc 15 section 4.3.",
                "",
                "WARNING: never place this folder in a synced or shared location",
                "while self-contained mode is active.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    tmp_zip = zip_path.with_suffix(".zip.tmp")
    try:
        # If an interrupted build left a stale .tmp behind, remove it first
        if tmp_zip.exists():
            tmp_zip.unlink(missing_ok=True)
        with zipfile.ZipFile(tmp_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=1) as zf:
            for path in sorted(payload.rglob("*")):
                if path.is_file():
                    zf.write(path, Path(APP_NAME) / path.relative_to(payload))
        # Ensure destination is unlinked if existing on Windows to avoid replacement locks
        if zip_path.exists():
            zip_path.unlink(missing_ok=True)
        tmp_zip.replace(zip_path)
    finally:
        flag_doc.unlink(missing_ok=True)
        if tmp_zip.exists():
            tmp_zip.unlink(missing_ok=True)
    return zip_path


# --------------------------------------------------------------------------
# Step 8 - SHA-256 + SBOM
# --------------------------------------------------------------------------


def write_checksums(out_dir: Path, version: str, artefacts: Sequence[Path]) -> Path:
    """Doc 15 section 3.2 step 8: "Compute SHA-256 of both artefacts; write
    `SHA256SUMS-<version>.txt`; attach the SBOM snapshot (`pip freeze`)".

    Doc 15 section 1.2 calls this file `SHA256SUMS-<version>.txt` and describes it
    as "Published with the artefacts; verified by the client before running".
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    sums = out_dir / f"SHA256SUMS-{version}.txt"
    lines = [
        f"# SHA-256 checksums for {DISPLAY_NAME} {version}",
        "# Verify before first use (doc 15 section 8.3):",
        '#   certutil -hashfile "<file>" SHA256',
        "# The digest below must match the one Windows reports, character for",
        "# character, or the package is not ours - stop and contact support.",
        "",
    ]
    for art in artefacts:
        if art and art.exists():
            lines.append(f"{sha256_of(art)}  {art.name}")
    sums.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return sums


def write_sbom(root: Path, out_dir: Path, version: str) -> Path | None:
    """The `sbom/py-<version>.txt` supply-chain artefact (doc 15 section 1.2,
    SEC-029 / SEC-047): a `pip freeze` snapshot of the frozen environment."""
    out_dir.mkdir(parents=True, exist_ok=True)
    sbom_dir = out_dir / "sbom"
    sbom_dir.mkdir(exist_ok=True)
    target = sbom_dir / f"py-{version}.txt"
    res = run([sys.executable, "-m", "pip", "freeze", "--all"], "pip freeze SBOM")
    if res.returncode != 0:
        log("pip freeze failed; SBOM not written")
        return None
    target.write_text(res.stdout, encoding="utf-8")
    return target


# --------------------------------------------------------------------------
# Step 6 - Inno Setup
# --------------------------------------------------------------------------


def build_installer(root: Path, version: str) -> Path | None:
    """Doc 15 section 3.2 step 6: "Inno Setup compile with
    `/DMyAppVersion=<version>`" -> `Setup-FPandAMonthEndCopilot-<version>.exe`."""
    iscc = find_iscc()
    if iscc is None:
        return None
    res = run(
        [iscc, f"/DMyAppVersion={version}", str(root / "packaging" / "installer.iss")],
        "Inno Setup compile",
        cwd=root / "packaging",
    )
    out = root / "packaging" / "out" / version / f"{INSTALLER_STEM}-{version}.exe"
    if res.returncode != 0 or not out.exists():
        print(res.stdout[-2000:])
        print(res.stderr[-2000:])
        return None
    return out


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the release artefacts.")
    parser.add_argument(
        "--dev", action="store_true", help="waive the clean-working-tree precondition"
    )
    parser.add_argument("--skip-installer", action="store_true", help="skip step 6 (Inno Setup)")
    parser.add_argument(
        "--skip-check", action="store_true", help="waive precondition 2 (scripts/check)"
    )
    parser.add_argument(
        "--no-smoke", action="store_true", help="skip step 9 (smoke test on the build host)"
    )
    args = parser.parse_args(argv)

    root = Path(__file__).resolve().parent.parent
    report = BuildReport()

    print("=== FP&A Month-End Copilot Build Pipeline ===")
    print(f"root={root}")
    print(f"host={sys.platform} python={sys.version.split()[0]}")
    print()

    # -- Preconditions (section 3.1). A failure here stops everything. ---------
    try:
        version = read_version(root)
        preconditions(root, args, version)
    except BuildError as exc:
        print(f"\nBUILD FAILED at preconditions: {exc}")
        return 1

    version_info = generate_version_info(root, version)
    log(f"generated {version_info.relative_to(root)} (version {version})")

    payload = root / "dist" / APP_NAME
    out_dir = root / "packaging" / "out" / version

    # -- Step 1: npm ci + npm run build ---------------------------------------
    t0 = time.perf_counter()
    log("step 1: build the UI")
    npm = which("npm")
    if npm is None:
        report.add(StageResult(1, "UI build", "fail", 0.0, errors=["npm is not on PATH"]))
        print(report.render())
        return 1
    ci = run([npm, "ci", "--prefix", "ui"], "npm ci")
    build = run([npm, "run", "build", "--prefix", "ui"], "npm run build")
    ok = ci.returncode == 0 and build.returncode == 0
    if not ok:
        print((build.stdout or "")[-3000:])
        print((build.stderr or "")[-3000:])
    report.add(
        StageResult(
            1,
            "UI build (npm ci + npm run build)",
            "pass" if ok else "fail",
            time.perf_counter() - t0,
            detail=f"ui/dist = {human(dir_size(root / 'ui' / 'dist'))}",
            errors=[] if ok else ["npm build failed; see transcript above"],
        )
    )

    # -- Step 2: copy ui/dist into app/static ---------------------------------
    t0 = time.perf_counter()
    app_static = root / "app" / "static"
    ui_dist = root / "ui" / "dist"
    if app_static.exists():
        shutil.rmtree(app_static)
    shutil.copytree(ui_dist, app_static)
    report.add(
        StageResult(
            2,
            "stage ui/dist into app/static",
            "pass",
            time.perf_counter() - t0,
            detail=f"{len(list(app_static.rglob('*')))} entries",
        )
    )
    log(f"rebuilt app/static ({dir_size(app_static):,} bytes)")

    # -- Step 3: PyInstaller onedir -------------------------------------------
    t0 = time.perf_counter()
    log("step 3: PyInstaller onedir packaging")
    if payload.exists():
        shutil.rmtree(payload)
    pyi = run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--noconfirm",
            str(root / "packaging" / "pyinstaller.spec"),
        ],
        "PyInstaller",
    )
    if pyi.returncode != 0 or not payload.is_dir():
        print((pyi.stdout or "")[-3000:])
        print((pyi.stderr or "")[-3000:])
        report.add(
            StageResult(
                3,
                "PyInstaller onedir",
                "fail",
                time.perf_counter() - t0,
                errors=["PyInstaller failed; see transcript above"],
            )
        )
        print(report.render())
        return 1
    report.add(
        StageResult(
            3,
            "PyInstaller onedir",
            "pass",
            time.perf_counter() - t0,
            detail=f"{human(dir_size(payload))} at dist/{APP_NAME}",
        )
    )

    # -- Step 4: stage the payload ---------------------------------------------
    t0 = time.perf_counter()
    staged, step4_blockers = stage_payload(root, payload, version)
    report.add(
        StageResult(
            4,
            "stage payload beside the exe",
            "fail" if step4_blockers else "pass",
            time.perf_counter() - t0,
            detail="staged: " + ", ".join(staged),
            blockers=step4_blockers,
        )
    )

    # -- Step 5: PAYLOAD AUDIT --------------------------------------------------
    t0 = time.perf_counter()
    audit_errors, audit_blockers, breakdown = audit_payload(root, payload)
    report.add(
        StageResult(
            5,
            "PAYLOAD AUDIT",
            "fail" if audit_errors else "pass",
            time.perf_counter() - t0,
            detail=(
                f"{len(REQUIRED_PAYLOAD_ENTRIES)} required entries checked; "
                f"{len(list(payload.rglob('*')))} payload paths scanned"
            ),
            errors=audit_errors,
            blockers=audit_blockers,
        )
    )

    # -- Step 6: Inno Setup -----------------------------------------------------
    t0 = time.perf_counter()
    if args.skip_installer:
        report.add(
            StageResult(
                6, "Inno Setup compile", "skip", time.perf_counter() - t0, detail="--skip-installer"
            )
        )
        installer = None
    else:
        installer = build_installer(root, version)
        report.add(
            StageResult(
                6,
                "Inno Setup compile",
                "pass" if installer else "fail",
                time.perf_counter() - t0,
                detail=f"{human(installer.stat().st_size)}" if installer else "compile failed",
                errors=[] if installer else ["Inno Setup compile failed"],
            )
        )

    # -- Step 7: portable zip ---------------------------------------------------
    t0 = time.perf_counter()
    zip_path = build_portable_zip(root, payload, out_dir, version)
    report.add(
        StageResult(
            7,
            "portable zip",
            "pass" if zip_path else "fail",
            time.perf_counter() - t0,
            detail=f"{zip_path.name} ({human(zip_path.stat().st_size)})" if zip_path else "",
        )
    )

    # -- Step 8: SHA-256 + SBOM -------------------------------------------------
    t0 = time.perf_counter()
    artefacts = [a for a in (installer, zip_path) if a]
    sums = write_checksums(out_dir, version, artefacts)
    sbom = write_sbom(root, out_dir, version)
    report.add(
        StageResult(
            8,
            "SHA-256 + SBOM",
            "pass" if sums else "fail",
            time.perf_counter() - t0,
            detail=(
                f"{sums.name} ({len(artefacts)} artefact(s)); "
                f"SBOM {sbom.name if sbom else 'NOT WRITTEN'}"
            ),
        )
    )

    # -- Step 9: smoke test -----------------------------------------------------
    t0 = time.perf_counter()
    smoke_ok, smoke_note = run_smoke(payload, skip=args.no_smoke)
    report.add(
        StageResult(
            9,
            "smoke test on the build host",
            "skip" if args.no_smoke else ("pass" if smoke_ok else "fail"),
            time.perf_counter() - t0,
            detail=smoke_note,
        )
    )

    # -- Step 10: size and time report vs NFR-006 -------------------------------
    t0 = time.perf_counter()
    size_report = write_size_report(
        out_dir,
        version,
        breakdown,
        dir_size(payload),
        installer,
        zip_path,
        report.stages,
    )
    report.add(
        StageResult(
            10,
            "size and time report vs NFR-006",
            "pass",
            time.perf_counter() - t0,
            detail=size_report.name,
        )
    )

    print()
    print(report.render())
    print()
    print(f"artefacts: {out_dir}")

    if report.failed:
        print("\nBUILD FAILED - see the failing stages above.")
        return 1
    print("\n=== Build complete ===")
    return 0


def run_smoke(payload: Path, skip: bool) -> tuple[bool, str]:
    """Doc 15 section 3.2 step 9: "Smoke test on the build host (install ->
    launch -> sample project -> generate one pack -> uninstall)".

    A full interactive smoke test needs a desktop session; this verifies the
    bundle is structurally launchable (exe present, PyInstaller runtime intact)
    and reports honestly that the interactive half was not exercised.
    """
    if skip:
        return True, "skipped by --no-smoke"
    exe = payload / f"{APP_NAME}.exe"
    if not exe.exists():
        return False, f"missing executable: {exe}"
    internal = payload / "_internal"
    if not (internal / "base_library.zip").exists() and not list(internal.glob("*.pyd")):
        return False, "PyInstaller runtime looks incomplete in _internal"
    return True, (
        "structural check only (exe + PyInstaller runtime present); the "
        "interactive install/launch/generate-pack/uninstall half needs a "
        "desktop session and is the clean-Windows-11 gate (doc 15 section 5)"
    )


def write_size_report(
    out_dir: Path,
    version: str,
    breakdown: dict[str, int],
    payload_bytes: int,
    installer: Path | None,
    zip_path: Path | None,
    stages: list[StageResult],
) -> Path:
    """Doc 15 section 3.2 step 10: "Size and time report: installer size vs
    `NFR-006`, build duration, payload breakdown by component"."""
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "build-report.md"
    total_duration = sum(s.seconds for s in stages)

    if installer and installer.exists():
        size = installer.stat().st_size
        verdict = "PASS" if size <= NFR_006_MAX_BYTES else "FAIL"
        measured = f"`{installer.name}` = {human(size)}"
    else:
        size = None
        verdict = "NOT VERIFIED"
        measured = (
            "No Inno Setup artefact was produced (`--skip-installer`, or Inno "
            "Setup is not installed). NFR-006 is defined on the installer "
            "(doc 14 line 84), so it is **NOT VERIFIED** by this run."
        )

    lines = [
        f"# Build report - {DISPLAY_NAME} {version}",
        "",
        f"Generated by `scripts/build` at {datetime.now(UTC).isoformat(timespec='seconds')}.",
        "",
        "## NFR-006 (installer <= 500 MB)",
        "",
        f"- Verdict: **{verdict}**",
        f"- Measured: {measured}",
        f"- Budget: {human(NFR_006_MAX_BYTES)}",
        "",
    ]
    if zip_path and zip_path.exists():
        lines += [
            f"- For reference only, the portable zip is "
            f"{human(zip_path.stat().st_size)}. This is NOT the artefact NFR-006",
            "  measures and is not offered as evidence of compliance.",
        ]
    lines += [
        "",
        "## PyInstaller payload",
        "",
        f"- Total: {human(payload_bytes)} ({payload_bytes:,} bytes)",
        "",
        "| Component | Size |",
        "|---|---|",
    ]
    for name, size_bytes in sorted(breakdown.items(), key=lambda kv: -kv[1]):
        lines.append(f"| `{name}` | {human(size_bytes)} |")

    lines += [
        "",
        "## Build duration",
        "",
        "| Step | Seconds |",
        "|---|---|",
    ]
    for s in stages:
        lines.append(f"| {s.number}. {s.name} | {s.seconds:.1f} |")
    lines.append(f"| **total** | **{total_duration:.1f}** |")

    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    log(f"NFR-006 verdict: {verdict}; report at {target}")
    return target


if __name__ == "__main__":
    sys.exit(main())
