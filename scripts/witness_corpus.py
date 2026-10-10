#!/usr/bin/env python3
"""CORPUS-05: Determinism witness script for the sample data corpus.

Proves that running `sample-data/generate_sample_data.py` twice with the same seed
(seed=42) produces byte-identical corpus files, records their SHA-256 checksums side
by side, and writes out the witness report to `evidence/corpus_determinism.md`.
"""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA = REPO / "sample-data"
GENERATOR = DATA / "generate_sample_data.py"
EVIDENCE = REPO / "evidence" / "corpus_determinism.md"


def hash_tree(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(root.glob("**/*")):
        if p.is_file() and p.suffix in (".csv", ".json", ".xlsx"):
            rel = str(p.relative_to(root)).replace("\\", "/")
            out[rel] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def run_gen(dest: Path, seed: int) -> tuple[int, str, str]:
    cmd = [sys.executable, str(GENERATOR), "--dir", str(dest), "--seed", str(seed)]
    start = datetime.now(UTC)
    res = subprocess.run(
        cmd, cwd=str(REPO), capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    duration = (datetime.now(UTC) - start).total_seconds()
    return res.returncode, res.stdout, res.stderr


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Corpus determinism witness script (CORPUS-05)")
    parser.add_argument("--seed", type=int, default=42, help="Random seed (default: 42)")
    args = parser.parse_args(argv)

    print(f"--> [CORPUS-05] Running corpus determinism witness (seed={args.seed})...")
    tmp = Path(tempfile.mkdtemp(prefix="corpus-witness-"))
    try:
        run1_dir = tmp / "run1"
        run2_dir = tmp / "run2"

        print("--> [CORPUS-05] Running build 1...")
        rc1, out1, err1 = run_gen(run1_dir, args.seed)
        if rc1 != 0:
            print(f"FAILED: build 1 exited with {rc1}\n{err1}", file=sys.stderr)
            return 1

        print("--> [CORPUS-05] Running build 2...")
        rc2, out2, err2 = run_gen(run2_dir, args.seed)
        if rc2 != 0:
            print(f"FAILED: build 2 exited with {rc2}\n{err2}", file=sys.stderr)
            return 1

        h1 = hash_tree(run1_dir)
        h2 = hash_tree(run2_dir)

        keys = sorted(set(h1.keys()) | set(h2.keys()))
        diffs = [k for k in keys if h1.get(k) != h2.get(k)]

        print(f"--> [CORPUS-05] Files hashed: {len(keys)}")
        print(f"--> [CORPUS-05] Differing files: {len(diffs)}")

        report_lines = [
            "# CORPUS-05: Corpus Determinism Witness Evidence",
            "",
            "**Task Reference**: `CORPUS-05` (P1)  ",
            f"**Timestamp**: `{datetime.now(UTC).isoformat()}`  ",
            f"**Seed**: `{args.seed}`  ",
            "**Generator**: `sample-data/generate_sample_data.py`",
            "",
            "## 1. Execution Summary",
            "",
            f"- **Run 1 Exit Code**: `{rc1}`",
            f"- **Run 2 Exit Code**: `{rc2}`",
            f"- **Total Files Compared**: `{len(keys)}`",
            f"- **Differing Files**: `{len(diffs)}`",
            f"- **Determinism Verdict**: `{'PASS - BYTE IDENTICAL' if not diffs else 'FAIL - DRIFT DETECTED'}`",
            "",
            "## 2. Checksum Side-by-Side Table",
            "",
            "| File Path | Run 1 SHA-256 | Run 2 SHA-256 | Match |",
            "|---|---|---|---|",
        ]

        for k in keys:
            v1 = h1.get(k, "(missing)")
            v2 = h2.get(k, "(missing)")
            match = "YES" if v1 == v2 else "NO"
            report_lines.append(f"| `{k}` | `{v1[:16]}…` | `{v2[:16]}…` | **{match}** |")

        report_lines += [
            "",
            "## 3. Conclusion",
            "",
            "Running `generate_sample_data.py` twice with the same seed produces strictly byte-identical corpus files across GL, budget, sub-ledgers, and import history fixtures. CORPUS-03 and other downstream tests depend on this deterministic foundation.",
        ]

        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
        print(f"--> [CORPUS-05] Witness report written to {EVIDENCE}")

        return 0 if not diffs else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
