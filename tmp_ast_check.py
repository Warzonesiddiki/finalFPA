import ast
import glob
import os

def check():
    tests_dir = r"C:\Users\Tahir\Documents\GitHub\finalFPA\tests"
    test_files = glob.glob(os.path.join(tests_dir, "**", "test_*.py"), recursive=True)
    
    offenders = []
    
    for filepath in test_files:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()
            
        tree = ast.parse(source, filename=filepath)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                for child in ast.walk(node):
                    if isinstance(child, ast.Try):
                        for handler in child.handlers:
                            is_bare = handler.type is None
                            is_exception = False
                            if handler.type is not None:
                                if isinstance(handler.type, ast.Name) and handler.type.id == "Exception":
                                    is_exception = True
                                elif isinstance(handler.type, ast.Tuple):
                                    for t in handler.type.elts:
                                        if isinstance(t, ast.Name) and t.id == "Exception":
                                            is_exception = True
                            
                            if is_bare or is_exception:
                                if len(handler.body) == 1 and isinstance(handler.body[0], ast.Pass):
                                    has_assert = any(isinstance(stmt, ast.Assert) for stmt in ast.walk(child))
                                    if has_assert:
                                        offenders.append(f"{os.path.basename(filepath)}:{handler.lineno} in {node.name}")

    print("Found:", offenders)

if __name__ == "__main__":
    check()
