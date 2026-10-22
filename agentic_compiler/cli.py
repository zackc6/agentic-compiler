"""``agentic-compiler`` command line.

    agentic-compiler pins                      # what the walk runs against
    agentic-compiler run CASE [-o OUT]         # one application-search walk
    agentic-compiler run-all [-o OUT]          # every case under cases/
    agentic-compiler serve OUT DIGEST          # lookup(%k) → artifact or fallback
    agentic-compiler check-contract            # lintel ⇄ choreo drift report
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .contract import CASES_DIR, LINTEL_DIR, pins
from .loop import load_case, walk
from .serve import Store, serve


def _cmd_pins(_: argparse.Namespace) -> int:
    print(json.dumps(pins().as_dict(), indent=2))
    return 0


def _run_one(case_path: Path, out_root: Path) -> dict:
    case = load_case(case_path)
    out_dir = out_root / case.name
    res = walk(case, out_dir)
    summary = res.summary()
    exp = case.expect
    ok = True
    if "decision" in exp and exp["decision"] != res.decision:
        ok = False
    if "walk" in exp and exp["walk"] != res.outcomes:
        ok = False
    summary["expected_ok"] = ok
    summary["expect"] = exp
    return summary


def _cmd_run(a: argparse.Namespace) -> int:
    s = _run_one(Path(a.case), Path(a.out))
    print(json.dumps(s, indent=2))
    return 0 if s["expected_ok"] else 1


def _cmd_run_all(a: argparse.Namespace) -> int:
    rc = 0
    rows = []
    for p in sorted(CASES_DIR.rglob("*.case.json")):
        s = _run_one(p, Path(a.out))
        rows.append(s)
        flag = "ok " if s["expected_ok"] else "BAD"
        print(f"{flag} {s['case']:<28} {s['decision']:<8} {' → '.join(s['walk'])}")
        rc |= 0 if s["expected_ok"] else 1
    (Path(a.out) / "run-all.json").write_text(json.dumps(rows, indent=2) + "\n")
    return rc


def _cmd_serve(a: argparse.Namespace) -> int:
    res = serve(Store(Path(a.out) / "store"), a.digest)
    print(
        json.dumps(
            {
                "hit": res.hit,
                "cache_key_digest": res.cache_key_digest,
                "artifact": str(res.artifact_path) if res.artifact_path else None,
                "kind": res.artifact_kind,
                "launch": res.launch,
                "fallback": res.fallback,
            },
            indent=2,
        )
    )
    return 0 if res.hit else 2


def _cmd_check_contract(_: argparse.Namespace) -> int:
    """Run Choreo's own consume-check against the pinned Lintel tree and print the drift."""
    from choreoir import consume_check

    problems = consume_check(LINTEL_DIR)
    print(json.dumps({"lintel": str(LINTEL_DIR), "problems": problems}, indent=2))
    print(f"\n{len(problems)} drift item(s). See docs/DRIFT.md.", file=sys.stderr)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="agentic-compiler", description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("pins").set_defaults(fn=_cmd_pins)

    r = sub.add_parser("run")
    r.add_argument("case")
    r.add_argument("-o", "--out", default="out")
    r.set_defaults(fn=_cmd_run)

    ra = sub.add_parser("run-all")
    ra.add_argument("-o", "--out", default="out")
    ra.set_defaults(fn=_cmd_run_all)

    s = sub.add_parser("serve")
    s.add_argument("out")
    s.add_argument("digest")
    s.set_defaults(fn=_cmd_serve)

    sub.add_parser("check-contract").set_defaults(fn=_cmd_check_contract)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
