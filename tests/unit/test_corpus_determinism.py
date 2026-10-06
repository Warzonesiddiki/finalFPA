"""Determinism of the sample corpus (QUAL-05, TB-021).

The same corpus, regenerated from the same seed, must produce byte-identical
files. `scripts/acceptance.py` records a run-to-run fingerprint of the CSV half
of the corpus precisely because nothing else did; this test makes that property
enforced rather than observed, and it covers the `.xlsx` half too.

Two separate clocks used to break this and both are pinned by
`sample-data.generate_sample_data.save_deterministic`:

  1. `docProps/core.xml`'s `dcterms:created`, and
  2. `dcterms:modified`, which openpyxl re-stamps inside `save()` itself, so
     setting the property beforehand does nothing.

Fixing (1) alone leaves `core.xml` looking reproducible while the SHA-256 still
moves, so the test asserts on the whole archive.

If this fails, a wall clock has leaked back into the corpus. Do not relax it.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
GENERATOR = REPO_ROOT / "sample-data" / "generate_sample_data.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location("fpa_sample_generator", GENERATOR)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _fingerprint(root: Path) -> dict[str, str]:
    """SHA-256 of every generated corpus artefact, keyed by relative path."""
    digests = {}
    for path in sorted(root.rglob("*")):
        if path.is_dir() or path.name == ".gitkeep":
            continue
        if path.suffix.lower() not in {".csv", ".xlsx", ".pptx"}:
            continue
        digests[path.relative_to(root).as_posix()] = hashlib.sha256(
            path.read_bytes()
        ).hexdigest()
    return digests


@pytest.fixture(scope="module")
def two_runs(tmp_path_factory):
    """Generate the corpus twice at the committed seed and fingerprint both."""
    generator = _load_generator()
    fingerprints = []
    for index in range(2):
        target = tmp_path_factory.mktemp(f"determinism_run{index}")
        generator.generate_dataset(str(target), scale=4000, seed=42)
        fingerprints.append(_fingerprint(target))
    return fingerprints


def test_corpus_regenerates_byte_identically(two_runs):
    first, second = two_runs
    assert first, "the generator produced no corpus files"
    assert first == second, (
        "corpus regeneration is not byte-reproducible; differing files: "
        + ", ".join(
            name for name in sorted(set(first) | set(second))
            if first.get(name) != second.get(name)
        )
    )


def test_xlsx_archives_are_byte_identical(two_runs):
    """The `.xlsx` half specifically: this is what TB-021 was about."""
    first, second = two_runs
    xlsx = {name for name in first if name.endswith(".xlsx")}
    assert xlsx, "expected .xlsx fixtures in the corpus"
    differing = [name for name in sorted(xlsx) if first[name] != second.get(name)]
    assert not differing, (
        "xlsx archives changed between runs; a wall clock is leaking into "
        f"docProps/core.xml or the zip entry headers: {differing}"
    )


def test_no_wall_clock_left_in_xlsx_core_properties(tmp_path):
    """A direct read of the property, not just a hash, so the cause is obvious."""
    generator = _load_generator()
    assert generator.save_deterministic is not None
    assert generator.XLSX_FIXED_TIMESTAMP.year == 2026

    import openpyxl

    workbook = openpyxl.Workbook()
    workbook.active.append(["Probe", 1])
    out = tmp_path / "probe.xlsx"
    generator.save_deterministic(workbook, out)

    import re
    import zipfile

    core = zipfile.ZipFile(out).read("docProps/core.xml").decode("utf-8")
    stamps = set(re.findall(r"<dcterms:(?:created|modified)[^>]*>([^<]*)<", core))
    stamps = {s for s in stamps if s}
    assert stamps == {generator.XLSX_FIXED_TIMESTAMP.strftime("%Y-%m-%dT%H:%M:%SZ")}, (
        f"expected a single pinned timestamp, found {stamps}"
    )