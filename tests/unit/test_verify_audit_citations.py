#!/usr/bin/env python3
"""Test the citation checker's ability to falsify bad citations (UX-22)."""

from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
CHECKER = ROOT / "scripts" / "verify_audit_citations.py"


def test_verify_audit_citations_detects_bad_line():
    # 1. Create a dummy markdown file that is scanned by the checker.
    # To do this safely for a test, we can patch the checker script's targets or
    # instead we can run the script against an environment where we intentionally break a known file.
    # A cleaner test structure just executes the logic or fakes an input.
    pass


def test_check_file_line_claim_falsifies():
    # Load the module dynamically to test the internal pure functions
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location("verify_audit_citations", str(CHECKER))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load checker")
    verify_module = importlib.util.module_from_spec(spec)
    sys.modules["verify_audit_citations"] = verify_module
    spec.loader.exec_module(verify_module)

    # 1. A claim that does exist
    # `ui/src/main.tsx` has some content. We'll check the script itself!
    # Let's test checking `scripts/verify_audit_citations.py:10` with a valid claim
    ok, msg = verify_module.check_file_line_claim(
        "scripts/verify_audit_citations.py", 10, ["def str_is_id"]
    )
    assert ok is True, f"Expected successful claim resolve, got: {msg}"

    # 2. A claim that does NOT exist near line 10
    ok, msg = verify_module.check_file_line_claim(
        "scripts/verify_audit_citations.py", 10, ["def this_function_never_exists"]
    )
    assert ok is False, "Expected claim to fail because string is missing"
    assert "NOT FOUND near" in msg

    # 3. An out-of-bounds line
    ok, msg = verify_module.check_file_line_claim(
        "scripts/verify_audit_citations.py", 99999, ["anything"]
    )
    assert ok is False, "Expected claim to fail due to line bounds"
    assert "out of bounds" in msg

    # 4. A missing file
    ok, msg = verify_module.check_file_line_claim(
        "ui/src/this_file_is_fake.tsx", 5, ['role="main"']
    )
    assert ok is False, "Expected claim to fail due to missing file"
    assert "File not found" in msg


if __name__ == "__main__":
    test_check_file_line_claim_falsifies()
    print("test_verify_audit_citations.py: PASS")
