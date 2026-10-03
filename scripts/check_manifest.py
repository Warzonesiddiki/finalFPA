import re
from pathlib import Path

manifest_path = Path("evidence/manifest.md").resolve()
content = manifest_path.read_text(encoding="utf-8")

invalid_items = []

for idx, line in enumerate(content.splitlines()):
    matches = re.finditer(r'\[([^\]]+)\]\(([^)]+)\)', line)
    for match in matches:
        link_target = match.group(2)
        # ignore internal anchor links and external URLs
        if link_target.startswith("#") or link_target.startswith("http"):
            continue
            
        # resolve relative to manifest directory
        target_path = (manifest_path.parent / link_target).resolve()
        
        if not target_path.exists():
            invalid_items.append((idx + 1, link_target, str(target_path).encode("utf-8", errors="ignore").decode()))

if not invalid_items:
    print("All manifest referenced files exist.")
else:
    print(f"Found {len(invalid_items)} missing files:")
    for line_num, target, target_path in invalid_items:
        print(f"Line {line_num}: {target}")
