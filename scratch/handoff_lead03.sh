#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

python scripts/team.py handoff \
  --claim buffy-20261005T1841Z-f219 \
  --task LEAD-03 \
  --verification "python -m pytest tests/unit/test_open_cited_lines.py -q (34 passed); python -m ruff check scripts/open_cited_lines.py tests/unit/test_open_cited_lines.py (All checks passed); python -m mypy scripts/open_cited_lines.py (Success, no issues); python scripts/check_doc_integrity.py (PASSED); python scripts/license_gate.py (exit 0); python scripts/open_cited_lines.py evidence/ops/lead-03-citation-audit.md --limit 0 (exit 0)" \
  --note "LEAD-03: the citation opener, the command the team can run on any deliverable to see the difference between cited and measured."
