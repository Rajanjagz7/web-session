"""A trade the ROBOT closed (reversal, breakeven stop, late square-off ...) must not be labelled "Manual Exit" in the Journal."""
import json, re, subprocess, pathlib

SRC = (pathlib.Path(__file__).parent / "public/static/journal.js").read_text()


def labels(reasons):
    em = re.search(r"const EXIT_MAP = \{.*?\};", SRC).group(0)
    fn = re.search(r"const exitLabel = .*?;\n", SRC, re.S).group(0)
    js = em + "\n" + fn + f"\nconsole.log(JSON.stringify({json.dumps(reasons)}.map(exitLabel)));"
    return json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)


def test_robot_exits_are_not_manual():
    got = labels(["STOP", "TSL", "TARGET", "MANUAL", "REVERSE", "BREAKEVEN", "SQUARE-OFF (late)", "SQUARE-OFF", "TIME", "WEIRD", "", None])
    assert got == ["SL", "TSL", "T2", "Manual Exit", "Reversal", "Breakeven", "Time Exit", "Time Exit", "Time Exit", "Weird", "Manual Exit", "Manual Exit"]


def test_share_exit_type_reads_exitReason():
    assert "(s.exitReason || s.exitWhy)" in SRC
