import os
from pathlib import Path

def find_orphaned_pyc():
    orphans = []
    pyc_files = list(Path(".").rglob("*.pyc"))
    
    for pyc in pyc_files:
        if "__pycache__" not in str(pyc):
            continue
            
        base_name = pyc.stem.split(".")[0]
        ext = ".py"
        src_path = pyc.parent.parent / (base_name + ext)
        
        if not src_path.exists():
            orphans.append(pyc)
            
    return orphans

if __name__ == "__main__":
    orphans = find_orphaned_pyc()
    print(f"Found {len(orphans)} orphans")
    for o in orphans:
        print(o)
