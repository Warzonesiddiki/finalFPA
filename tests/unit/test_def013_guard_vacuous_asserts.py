import ast
from pathlib import Path

import pytest


def _is_bare_exception_pass(handler: ast.ExceptHandler) -> bool:
    """Return True when *handler* is `except Exception: pass` (or bare `except:`)."""
    if handler.type is not None and isinstance(handler.type, ast.Name) and handler.type.id != "Exception":
        return False
    return len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass)


def _try_contains_assert(try_node: ast.Try) -> bool:
    """Return True when any Assert lives inside *try_node*."""
    return any(isinstance(n, ast.Assert) for n in ast.walk(try_node))


def test_def013_guard_no_swallowed_assertions():
    """Guard DEF-013: no test may silently swallow an assertion."""
    tests_dir = Path("tests")
    offenders: list[str] = []

    for py_file in tests_dir.glob("**/test_*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except Exception:
            continue

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            for subnode in ast.walk(node):
                if isinstance(subnode, ast.Try):
                    for handler in subnode.handlers:
                        if _is_bare_exception_pass(handler) and _try_contains_assert(subnode):
                            offenders.append(f"{py_file.name}::{node.name}")

    if offenders:
        pytest.fail(
            f"DEF-013 Meta-Guard: Found tests wrapping assertions with bare 'except Exception: pass': {', '.join(offenders)}"
        )
