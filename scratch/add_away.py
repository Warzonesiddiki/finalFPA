"""Add an `away` list: a seat that is out (quota ended, offline) must not be treated
as idle, or the leader view and the watchdog will nag an agent who cannot answer all
day - which is how a supervision tool becomes noise nobody reads.

Changes:
  team/config.json        away: {agent: reason}
  scripts/team.py         leader view shows AWAY, and never lists an away seat as idle
  scripts/team_watchdog.py  survey marks the seat away; decide() never nudges it
"""
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
DQ = chr(34)
SQ = chr(39)
NL = chr(10)

# ---------------------------------------------------------------- config
cfgp = pathlib.Path("team/config.json")
cfg = json.loads(cfgp.read_text(encoding="utf-8"))
cfg["away"] = {
    "antigravity": "quota ended for 2026-10-05; stream parked, verification lane reassigned to hermes/buffy",
}
cfgp.write_text(json.dumps(cfg, indent=2) + NL, encoding="utf-8", newline="")
print("away:", list(cfg["away"]))

# ---------------------------------------------------------------- team.py leader view
tp = pathlib.Path("scripts/team.py")
src = tp.read_text(encoding="utf-8")
old_state = '        state = "working" if mine else "IDLE"'
assert src.count(old_state) == 1, "state anchor"
new_state = (
    '        away = cfg.get("away", {}).get(a)' + NL
    + '        state = "working" if mine else ("AWAY" if away else "IDLE")'
)
src = src.replace(old_state, new_state, 1)
old_idle = '        if not mine:' + NL + '            idle.append(a)'
assert src.count(old_idle) == 1, "idle anchor"
src = src.replace(old_idle, '        if not mine and not away:' + NL + '            idle.append(a)', 1)
tp.write_text(src, encoding="utf-8", newline="")
print("team.py: leader view knows about away seats")

# ---------------------------------------------------------------- watchdog
wp = pathlib.Path("scripts/team_watchdog.py")
w = wp.read_text(encoding="utf-8")
a1 = '        stream = [i for i in (cfg.get("streams", {}).get(a) or [])'
assert w.count(a1) == 1, "survey anchor"
w = w.replace(a1, '        is_away = bool(cfg.get("away", {}).get(a))' + NL + '        stream = [i for i in (cfg.get("streams", {}).get(a) or [])', 1)
a2 = '            "stream_claimable": claimable_stream,'
assert w.count(a2) == 1, "survey field anchor"
w = w.replace(a2, '            "stream_claimable": claimable_stream,' + NL + '            "away": is_away,', 1)
a3 = '    for agent, info in s["agents"].items():' + NL + '        if info["active_claims"]:' + NL + '            continue'
assert w.count(a3) == 1, "decide loop anchor"
w = w.replace(a3, '    for agent, info in s["agents"].items():' + NL
              + '        if info.get("away"):' + NL
              + '            # out of quota or offline: nagging an agent who cannot answer is noise' + NL
              + '            continue' + NL
              + '        if info["active_claims"]:' + NL
              + '            continue', 1)
wp.write_text(w, encoding="utf-8", newline="")
print("team_watchdog.py: away seats are skipped")
