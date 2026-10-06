"""`TB-026` slice 1 — the `R12` guard for the whole engine: one implementation per capability.

`TB-026` asks for `engine/common/` plus "the single-implementation test". A measurement of the current tree
(`evidence/tb026/survey.md`, 2026-10-05) shows the **consolidation is largely already done**: `quantize_money`
has one home (`calc/math.py`), `period_end_from_id`/`resolve_as_of_date` one home (`rules_01_08.py`), and the
dedupe normalisation moved to one home by `WC-1`. What is missing is the thing that *keeps* it that way — a
test that fails the moment a second copy of a helper appears.

That is this file. It is deliberately behaviour-free: it re-implements nothing, rewires nothing, and cannot
change product behaviour. It walks `app/engine/**.py` with `ast`, records every function definition by name,
and fails on any name defined in more than one place that is not on a documented allowlist.

**Why allowlist rather than "zero duplicates":** dataclass/serialiser hooks (`to_dict`, `__post_init__`) and
per-module database helpers (`_get_conn`, `_ensure_table`) are duplication *by nature* — two dataclasses each
having `to_dict` is not two implementations of one capability. Those are listed with the reason. Two entries
are real follow-ups and say so in their reason: `check_banned_phrases` and `split_sentences`.
"""

from __future__ import annotations

import ast
import collections
import pathlib

ENGINE = pathlib.Path(__file__).resolve().parents[2] / "app" / "engine"

#: name -> why more than one definition is legitimate (or which agent owes the consolidation)
ALLOWED_DUPLICATES: dict[str, str] = {
    "to_dict": "per-DTO serialiser - one per dataclass by nature",
    "__post_init__": "dataclass hook - one per dataclass by nature",
    "__init__": "constructor - one per class by nature (24 classes in the engine)",
    "_get_conn": "ai/ modules each own their DuckDB connection helper (different lifetimes)",
    "_ensure_table": "ai/ modules each bootstrap their own schema (different tables)",
    "generate": "different classes, different outputs (ai client method)",
    "run_rules": "acceptance harness vs exceptions repository are different layers",
    "lock_version": "forecast scenario version lock vs store row lock - different locks",
    "check_banned_phrases": "FOLLOW-UP: consolidate into ai/guardrails (owner to assign)",
    "split_sentences": "FOLLOW-UP: consolidate into one text helper; ai/guardrails owns it",
}

#: names whose multiplicity is the design (one evaluator per catalog rule, batch runners, …)
IGNORED_PREFIXES = ("evaluate", "run_", "test_", "_test", "tst_", "def_")


def definitions() -> dict[str, list[str]]:
    """Module- and class-level function definitions under ``app/engine``.

    Nested (closure) functions are deliberately **not** counted: a local ``def extract`` inside two
    different methods is two private helpers, not two implementations of one capability. Counting them
    produced a false positive on ``app/engine/ai/client.py`` (2026-10-05).
    """
    found: dict[str, list[str]] = collections.defaultdict(list)
    for path in sorted(ENGINE.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        rel = path.relative_to(ENGINE.parents[1]).as_posix()
        scopes: list[ast.AST] = list(tree.body)
        for scope in scopes:
            if isinstance(scope, ast.ClassDef):
                scopes.extend(scope.body)  # type: ignore[arg-type]
        for node in scopes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # ``@overload`` stubs are type declarations, not implementations: two of
                # them plus one real body is the correct pattern (excel_pack._coerce_money,
                # found by this guard on 2026-10-05). Only undecorated defs are counted.
                if _decorator_names(node) & {"overload", "typing.overload"}:
                    continue
                found[node.name].append(f"{rel}:{node.lineno}")
    return dict(found)


def _decorator_names(node: ast.AST) -> set[str]:
    names: set[str] = set()
    for dec in getattr(node, "decorator_list", []):
        target = dec.func if isinstance(dec, ast.Call) else dec
        parts = []
        while isinstance(target, ast.Attribute):
            parts.append(target.attr)
            target = target.value
        if isinstance(target, ast.Name):
            parts.append(target.id)
        names.add(".".join(reversed(parts)))
    return names


def unexpected_duplicates(defs: dict[str, list[str]]) -> dict[str, list[str]]:
    return {
        name: sites
        for name, sites in defs.items()
        if len(sites) > 1
        and name not in ALLOWED_DUPLICATES
        and not name.startswith(IGNORED_PREFIXES)
    }


def test_engine_walk_is_not_vacuous():
    """A guard that scans nothing passes for the wrong reason. Pin the scan's reach."""
    defs = definitions()
    assert len(defs) > 150, f"expected a real walk of app/engine, found only {len(defs)} function names"
    modules = list(ENGINE.rglob("*.py"))
    assert len(modules) > 40, f"expected >40 engine modules, found {len(modules)}"
    assert any(n.startswith("evaluate_exc_") for n in defs), "rule evaluators missing from the scan"


def test_no_capability_is_defined_twice():
    """The `R12` rule, mechanically: one implementation per capability in the engine."""
    dups = unexpected_duplicates(definitions())
    assert not dups, "duplicate implementations (R12) - consolidate, or document on ALLOWED_DUPLICATES:\n" + (
        "\n".join(f"  {name}: {', '.join(sites)}" for name, sites in sorted(dups.items()))
    )


def test_allowlist_is_still_accurate():
    """An allowlist that lists names nobody duplicates any more is a stale excuse (and hides regressions)."""
    dups = {n: s for n, s in definitions().items() if len(s) > 1}
    for name in ALLOWED_DUPLICATES:
        assert name in dups, f"ALLOWED_DUPLICATES lists {name!r}, which is no longer defined twice"


def test_money_helper_has_one_home():
    """Money is `R8`: exactly one `quantize_money`, and it must be the `calc/math.py` one."""
    sites = definitions()["quantize_money"]
    assert len(sites) == 1, f"quantize_money defined {len(sites)} times: {sites}"
    assert sites[0].startswith("app/engine/calc/math.py"), sites[0]


def test_period_helpers_have_one_home():
    """Period maths is money-adjacent: one implementation each, not a copy per rule module."""
    for name in ("period_end_from_id", "resolve_as_of_date"):
        sites = definitions()[name]
        assert len(sites) == 1, f"{name} defined {len(sites)} times: {sites}"
        assert sites[0].startswith("app/engine/rules/rules_01_08.py"), f"{name}: {sites[0]}"


def test_dedupe_normalisation_has_one_home():
    """`WC-1` outcome: one implementation of the `06` `EXC-007` clause, plus a delegating alias."""
    defs = definitions()
    assert len(defs["normalise_invoice_no"]) == 1, defs["normalise_invoice_no"]
    assert defs["normalise_invoice_no"][0].startswith("app/engine/dedupe/normalize.py")
    # The legacy spelling may exist only as an alias, never as a second implementation.
    assert "_normalize_invoice_no" not in defs, (
        "the legacy _normalize_invoice_no is defined again — it must be an alias of normalise_invoice_no"
    )

def test_overload_stubs_are_not_counted_as_implementations(tmp_path):
    """The exemption must stay narrow: @overload stubs are declarations, a second real
    body is still a duplicate. Proven by building both shapes and scanning them."""
    import importlib.util

    src = importlib.util.spec_from_file_location("t_engine_common_probe", __file__)
    mod = importlib.util.module_from_spec(src)
    src.loader.exec_module(mod)
    original_engine = mod.ENGINE
    try:
        good = tmp_path / "app" / "engine" / "good.py"
        good.parent.mkdir(parents=True)
        good.write_text(
            "from typing import overload" + chr(10) * 2
            + "@overload" + chr(10) + "def f(x: None) -> None: ..." + chr(10)
            + "@overload" + chr(10) + "def f(x: int) -> int: ..." + chr(10)
            + "def f(x):" + chr(10) + "    return x" + chr(10),
            encoding="utf-8",
        )
        mod.ENGINE = good.parent
        good_hits = mod.definitions().get("f", [])
        assert len(good_hits) == 1 and good_hits[0].startswith("app/engine/good.py:"), good_hits

        bad = tmp_path / "app" / "engine" / "bad.py"
        bad.write_text(
            "def f(x):" + chr(10) + "    return x" + chr(10) * 2
            + "def f(x):" + chr(10) + "    return x" + chr(10),
            encoding="utf-8",
        )
        bad_hits = [h for h in mod.definitions().get("f", []) if h.startswith("app/engine/bad.py:")]
        assert len(bad_hits) == 2, bad_hits
    finally:
        mod.ENGINE = original_engine
