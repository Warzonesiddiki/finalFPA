import ast
from pathlib import Path
import pytest

def test_def013_guard_no_swallowed_assertions():
    tests_dir = Path("tests")
    offenders = []
    
    for py_file in tests_dir.glob("**/test_*.py"):
        try:
            content = py_file.read_text(encoding="utf-8")
            tree = ast.parse(content)
        except Exception:
            continue
            
        for node in ast.walk(tree):
            # Look for function definitions
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                # Walk the body of the test searching for Try blocks
                for subnode in ast.walk(node):
                    if isinstance(subnode, ast.Try):
                        # check if it uses except Exception: pass or except: pass
                        for handler in subnode.handlers:
                            if handler.type is None or (isinstance(handler.type, ast.Name) and handler.type.id == "Exception"):
                                # Check if body contains an Assert or just pass
                                # But wait, the defect specifically is wrapping an assert inside try-except Exception: pass
                                # Let's see if the handler just passes
                                if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                                    # Does the try body contain any assert?
                                    contains_assert = any(isinstance(n, ast.Assert) for n in ast.walk(subnode))
                                    if contains_assert:
                                        offenders.append(f"{py_file.name}::{node.name}")

    if offenders:
        pytest.fail(f"DEF-013 Meta-Guard: Found tests wrapping assertions with bare 'except Exception: pass': {', '.join(offenders)}")
