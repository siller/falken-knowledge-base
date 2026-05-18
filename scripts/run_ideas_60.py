"""Führt 60 Brainstorm-Fragen durch die Pipeline + speichert alles inkl. SQL+rows.

Nicht-validierend (kein check_pass) — Output ist menschlich lesbar, damit ich
echte Halluzinationen / leere / unsinnige Antworten manuell finden kann.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml

from falken_kb.genai.orchestrator import answer


def run(input_file: str = "tests/ideas_60.yaml", output_file: str = "tests/ideas_60_results.json"):
    questions = yaml.safe_load(Path(input_file).read_text())
    print(f"Lade {len(questions)} Brainstorm-Fragen...")
    results = []
    for i, q in enumerate(questions, 1):
        t0 = time.time()
        try:
            r = answer(q["question"])
            r["time_sec"] = round(time.time() - t0, 1)
            r["id"] = q["id"]
            r["category"] = q["category"]
            r["question"] = q["question"]
        except Exception as e:
            r = {"id": q["id"], "category": q["category"], "question": q["question"],
                 "error": str(e)[:300], "time_sec": round(time.time() - t0, 1)}
        ans_short = (r.get("answer", "") or "")[:80].replace("\n", " ")
        if "error" in r and not r.get("answer"):
            ans_short = f"💥 {r['error'][:80]}"
        print(f"  [{i:>2}/{len(questions)}] {r['category']:<15} {r['question'][:60]:<60} → {ans_short[:80]}")
        results.append(r)
        # Throttle (höher weil parallel v4 läuft + Rate-Limit-Schutz)
        time.sleep(4)
        if i % 10 == 0:
            Path(output_file).write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str))

    Path(output_file).write_text(json.dumps(results, indent=2, ensure_ascii=False, default=str))
    print(f"\nGespeichert: {output_file}")


if __name__ == "__main__":
    run()
