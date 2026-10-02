import re

with open('docs/00_INDEX.md', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if line.startswith('| K-S2 |'):
        new_lines.append('| K-S2 | Product & client context: current manual workflow, Windows 11 x64, non-technical user, offline, self-contained installer, clean start | `01`, `21`, `22` | INTEGRATED (docs `01`, `21`, `22`, `23`, `25` complete) |\n')
    elif line.startswith('| K-S5 |'):
        new_lines.append('| K-S5 | Phase 0 documentation set & quality gate (the doc tree, gate checklist) | `00`, `14` | INTEGRATED (docs `00`–`30` complete; all 6 gates verified green in `14` §15) |\n')
    elif line.startswith('| A1-O |'):
        new_lines.append('| A1-O | Combined Phase 0 quality gate deltas (12 checks) | `00`, `14` | INTEGRATED (verified 12/12 in `14` §15.2) |\n')
    else:
        new_lines.append(line)

with open('docs/00_INDEX.md', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Index successfully updated.')
