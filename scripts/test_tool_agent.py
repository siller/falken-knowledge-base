"""Tool-Agent Stress-Test mit 20 diversen Fragen."""
from __future__ import annotations

import json
import sys
import time
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.genai.orchestrator import answer

TESTS = [
    ("db_simple_1", "Auf welchem Platz beendeten die Falken Saison 2022/23?", ["12"]),
    ("db_simple_2", "Wer war Topscorer der Falken in der Saison 2019/20?", ["Wruck"]),
    ("db_simple_3", "Wer war Trainer 2018/19?", ["Mellitzer"]),
    ("db_simple_4", "Wie viele Saisons spielten die Falken in der DEL2?", ["10"]),
    ("db_simple_5", "Was ist die aktuelle Liga der Falken?", ["Oberliga"]),
    ("db_agg_1", "In welcher Saison hatten die Falken die meisten Punkte aller Zeiten?", ["131", "132", "23", "24"]),
    ("db_agg_2", "Welcher Spieler hat die meisten Karriere-Punkte für die Falken?", ["Kirsch", "Wittmann"]),
    ("po_1", "Wer gewann die Halbfinale-Serie zwischen Falken und Hannover Scorpions 2024/25?", ["Hannover"]),
    ("po_2", "Wie weit kamen die Falken in den Oberliga-Süd Playoffs 2024/25?", ["Halbfinale", "Hannover"]),
    ("game_1", "Welches Ergebnis hatte das Spiel ECDC Memmingen vs Falken am 27.02.2026?", ["7:2", "Memmingen"]),
    ("player_1", "Wie viele Saisons spielte Nolan Ritchie für die Falken?", ["2 Saison", "zwei Saison", "2024", "2025"]),
    ("player_2", "Was war die beste Saison von Dylan Wruck?", ["2019", "88"]),
    ("news_1", "Wer ist Steffen Ziesche?", ["Trainer"]),
    ("news_2", "Was ist die neueste News zu den Falken?", ["Falken"]),
    ("news_3", "Was ist über Franz Jokinen bei den Falken bekannt?", ["Jokinen"]),
    ("mh_1", "Wann hat der jetzige Besitzer der Tenno Sushi Bar bei den Falken gespielt?", ["Gödtel", "2014"]),
    ("oos_1", "Wer wurde 2025 Deutscher Eishockey-Meister?", []),
    ("edge_1", "Hat Calder Anderson in 25/26 mehr Tore als Vorlagen?", ["Anderson"]),
    ("edge_2", "Welche Falken-Spieler hatten mehr als 80 Punkte in einer Saison?", ["Wernerson", "Ritchie", "Wruck"]),
    ("edge_3", "Wie viele unterschiedliche Trainer hatten die Falken in der DEL2-Zeit?", ["Trainer"]),
]


def run():
    results = []
    for tid, q, expected_keywords in TESTS:
        t0 = time.time()
        record = {"id": tid, "question": q, "expected_keywords": expected_keywords}
        try:
            r = answer(q)
            dt = time.time() - t0
            record["time_sec"] = round(dt, 1)
            record["answer"] = r.get("answer", "")
            record["iterations"] = r.get("iterations", 0)
            trace = r.get("tool_trace", [])
            record["tool_chain"] = " → ".join(s.get("tool_name", s.get("action", "final")) for s in trace)
            ans_low = record["answer"].lower()
            matches = [k for k in expected_keywords if k.lower() in ans_low]
            record["matched"] = matches
            if expected_keywords:
                record["pass"] = bool(matches)
            else:
                # OOS: passt wenn "nicht/keine" Antwort
                record["pass"] = any(w in ans_low for w in ("nicht", "keine", "kein", "weiß nicht", "verfüg"))
        except Exception as e:
            record["time_sec"] = round(time.time() - t0, 1)
            record["error"] = str(e)[:300]
            record["pass"] = False
        marker = "✓" if record.get("pass") else "✗"
        print(f"[{marker}] {tid:<14} {record['time_sec']:>5}s  it={record.get('iterations',0)}  chain={record.get('tool_chain','-')[:60]}", flush=True)
        print(f"     A: {record.get('answer','')[:150]}", flush=True)
        if not record.get("pass") and "error" in record:
            print(f"     ✗ ERR: {record['error'][:120]}", flush=True)
        elif not record.get("pass"):
            print(f"     ✗ missing: {expected_keywords}", flush=True)
        print(flush=True)
        results.append(record)
        time.sleep(5)  # höhere Throttle damit DGX nicht überlastet

    pass_n = sum(1 for r in results if r.get("pass"))
    fail_n = len(results) - pass_n
    print(f"\n=== Final: {pass_n}/{len(TESTS)} = {100*pass_n/len(TESTS):.0f}% ===")
    Path("tests/tool_agent_results.json").write_text(
        json.dumps({"summary": {"pass": pass_n, "fail": fail_n, "total": len(TESTS)}, "results": results},
                   indent=2, ensure_ascii=False, default=str))
    return pass_n, fail_n


if __name__ == "__main__":
    run()
