"""Führt sowohl tests/ground_truth.yaml als auch tests/ground_truth_auto.yaml aus."""
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql
from falken_kb.validation import _matches


def run_file(path: Path) -> dict:
    checks = yaml.safe_load(path.read_text())
    pass_n = 0
    fail_n = 0
    fails = []
    for c in checks:
        try:
            actual = exec_sql(c["query"])
            if _matches(actual, c["expected"]):
                pass_n += 1
            else:
                fail_n += 1
                fails.append({"id": c["id"], "desc": c["description"], "expected": c["expected"], "actual": actual})
        except Exception as e:
            fail_n += 1
            fails.append({"id": c["id"], "desc": c["description"], "error": str(e)[:200]})
    return {"file": path.name, "total": len(checks), "pass": pass_n, "fail": fail_n, "failures": fails}


def main():
    root = Path(__file__).resolve().parent.parent / "tests"
    for f in ["ground_truth.yaml", "ground_truth_auto.yaml"]:
        path = root / f
        if not path.exists():
            continue
        r = run_file(path)
        print(f"\n=== {r['file']}: {r['pass']}/{r['total']} PASS ({100*r['pass']/r['total']:.1f}%) ===")
        if r["failures"]:
            print(f"  FAILS:")
            for f_ in r["failures"][:20]:
                print(f"    ✗ [{f_['id']}] {f_['desc']}")
                if "error" in f_:
                    print(f"        ERROR: {f_['error'][:120]}")
                else:
                    print(f"        Expected: {f_['expected']}")
                    print(f"        Actual:   {f_['actual']}")


if __name__ == "__main__":
    main()
