"""Append the two away-seat tests to tests/unit/test_team_watchdog.py (write_file keeps
the nested quoting intact, which is what the heredoc could not do)."""
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")
NL = chr(10)
Q = chr(34)
TQ = Q * 3

target = pathlib.Path("tests/unit/test_team_watchdog.py")
text = target.read_text(encoding="utf-8")
if "test_an_away_seat_is_never_nudged" in text:
    print("already appended")
    raise SystemExit(0)

block = [
    "",
    "",
    "def test_an_away_seat_is_never_nudged():",
    "    " + TQ + "A seat that is out of quota cannot answer a nudge, so a loop that pings it all",
    "    day trains the team to ignore the loop. An away seat is skipped entirely." + TQ,
    "    info = agent_info(stream=[" + Q + "RV-02" + Q + "], claimable=[" + Q + "RV-02" + Q + "], idle=600)",
    "    info[" + Q + "away" + Q + "] = True",
    "    s = survey({" + Q + "antigravity" + Q + ": info})",
    "    assert wd.decide(s, {" + Q + "nudges" + Q + ": {}}, cfg()) == []",
    "",
    "",
    "def test_the_same_seat_is_nudged_when_it_is_not_away():",
    "    " + TQ + "The away flag must not become a permanent mute: drop it and the nudge returns." + TQ,
    "    s = survey({" + Q + "antigravity" + Q + ": agent_info(",
    "        stream=[" + Q + "RV-02" + Q + "], claimable=[" + Q + "RV-02" + Q + "], idle=600)})",
    "    assert [a[" + Q + "to" + Q + "] for a in wd.decide(s, {" + Q + "nudges" + Q + ": {}}, cfg())] == ["
    + Q + "antigravity" + Q + "]",
    "",
]
target.write_text(text.rstrip() + NL + NL.join(block), encoding="utf-8", newline="")
print("2 away tests appended")
