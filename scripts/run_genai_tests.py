"""Führt alle 211 Test-Fragen gegen die GenAI-Pipeline + protokolliert Halluzinationen."""
import json
import re
import sys
import time
from pathlib import Path

import httpx
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.genai.orchestrator import answer


def wait_for_dgx(max_wait_min: int = 60) -> bool:
    """Polled DGX bis es wieder up ist (oder timeout)."""
    end = time.time() + max_wait_min * 60
    while time.time() < end:
        try:
            r = httpx.post(
                "https://pgxapi.siller.io/v1/chat/completions",
                headers={"Authorization": "Bearer sk-AboUkuaAghVTt_vnPIDqoQ", "Content-Type": "application/json"},
                json={"model": "gemma-4-31B", "max_tokens": 3, "messages": [{"role": "user", "content": "hi"}]},
                timeout=10,
            )
            if r.status_code == 200:
                return True
        except httpx.HTTPError:
            pass
        time.sleep(30)
    return False


DOWN_SIGNALS = [
    "502", "503", "504", "app_down", "no route", "connectioninputs",
    "DOCTYPE", "App Error", "currently not responding",
    "remote_protocol_error", "json could not be generated",
]

def _is_outage(msg: str) -> bool:
    m = msg.lower()
    return any(s.lower() in m for s in DOWN_SIGNALS)


def answer_with_retry(question: str, max_attempts: int = 5):
    """answer() mit Retry bei DGX/Supabase-Outages."""
    last_err = None
    for attempt in range(max_attempts):
        try:
            return answer(question)
        except Exception as e:
            last_err = e
            msg = str(e)[:500]
            if _is_outage(msg):
                wait_min = 60
                print(f"      ⚠ Outage detected (attempt {attempt+1}/{max_attempts}), warte bis zu {wait_min}min auf Recovery...")
                if not wait_for_dgx(max_wait_min=wait_min):
                    print(f"      ⚠ Recovery-Timeout, sleep 60s + nächster Versuch")
                    time.sleep(60)
            else:
                # Nicht-Outage-Fehler — sofort raisen
                raise
    raise last_err


# Deutsche Zahl-Wörter → Ziffer (Cardinal + Ordinal).
# Substring-Match in extract_numbers reicht hier — wir wollen "zwölften" auch
# als 12 zählen, also matchen wir die Wortstämme.
GERMAN_NUMBERS = {
    "eins": 1, "einer": 1, "eine": 1, "erste": 1, "ersten": 1, "erster": 1, "erstem": 1,
    "zwei": 2, "zweite": 2, "zweiten": 2, "zweiter": 2,
    "drei": 3, "dritte": 3, "dritten": 3, "dritter": 3,
    "vier": 4, "vierte": 4, "vierten": 4, "vierter": 4,
    "fünf": 5, "fuenf": 5, "fünfte": 5, "fünften": 5, "fünfter": 5,
    "sechs": 6, "sechste": 6, "sechsten": 6, "sechster": 6,
    "sieben": 7, "siebte": 7, "siebten": 7, "siebter": 7,
    "acht": 8, "achte": 8, "achten": 8, "achter": 8,
    "neun": 9, "neunte": 9, "neunten": 9, "neunter": 9,
    "zehn": 10, "zehnte": 10, "zehnten": 10, "zehnter": 10,
    "elf": 11, "elfte": 11, "elften": 11, "elfter": 11,
    "zwölf": 12, "zwoelf": 12, "zwölfte": 12, "zwölften": 12, "zwoelfte": 12,
    "dreizehn": 13, "dreizehnte": 13, "dreizehnten": 13,
    "vierzehn": 14, "vierzehnten": 14,
    "fünfzehn": 15, "fuenfzehn": 15, "fünfzehnten": 15,
    "sechzehn": 16, "sechzehnten": 16,
}


def extract_numbers(text: str) -> set[str]:
    """Gibt alle Zahlen im Text als String-Set zurück (Ziffern + Deutsche Wörter)."""
    t = text.lower()
    nums = set(re.findall(r"\d+", t))
    # Wort-Matches per word-boundary
    for word, n in GERMAN_NUMBERS.items():
        if re.search(rf"\b{re.escape(word)}\b", t):
            nums.add(str(n))
    return nums


def check_pass(answer_text: str, expected_facts: list[str]) -> tuple[bool, list[str]]:
    """Prüft ob die Antwort die erwarteten Fakten enthält.

    - Numerische Fakten: matchen gegen extract_numbers (handles "ersten" → 1)
    - Text-Fakten: simple substring-match (case-insensitive)
    - Pass wenn min. 1 erwarteter Fakt enthalten ist.
    """
    a = (answer_text or "").lower()
    a_nums = extract_numbers(a) if answer_text else set()
    found = []
    missing = []
    for fact in expected_facts:
        f = str(fact).strip()
        f_low = f.lower()
        if f.isdigit():
            if f in a_nums:
                found.append(fact)
            else:
                missing.append(fact)
        else:
            if f_low in a:
                found.append(fact)
            else:
                missing.append(fact)
    return (len(found) > 0, missing)


def run(questions_file: str, output_file: str, limit: int | None = None) -> None:
    questions = yaml.safe_load(Path(questions_file).read_text())
    if limit:
        questions = questions[:limit]
    print(f"Lade {len(questions)} Test-Fragen...")

    results = []
    pass_count = 0
    fail_count = 0
    error_count = 0
    t_total_start = time.time()

    for i, q in enumerate(questions, 1):
        t0 = time.time()
        result = {
            "id": q["id"],
            "category": q["category"],
            "question": q["question"],
            "expected_facts": q["expected_facts"],
            "expected_category": q.get("expected_category"),
        }
        try:
            ans = answer_with_retry(q["question"])
            result["actual_answer"] = ans.get("answer", "")
            result["actual_category"] = ans.get("category")
            result["sql"] = ans.get("sql")
            result["time_sec"] = round(time.time() - t0, 1)
            passed, missing = check_pass(ans.get("answer", ""), q["expected_facts"])
            result["pass"] = passed
            result["missing_facts"] = missing
            if passed:
                pass_count += 1
                marker = "✓"
            else:
                fail_count += 1
                marker = "✗"
        except Exception as e:
            result["error"] = str(e)[:300]
            result["pass"] = False
            error_count += 1
            marker = "💥"

        elapsed = time.time() - t_total_start
        avg_per_q = elapsed / i
        eta = avg_per_q * (len(questions) - i)
        print(f"  [{i:>3}/{len(questions)}] {marker} {q['category']:<14} {q['question'][:70]:<70} "
              f"(t={result.get('time_sec',0):>4}s, eta {eta/60:.0f}min, P={pass_count} F={fail_count} E={error_count})")
        results.append(result)

        # Incremental save (für lange Runs)
        if i % 10 == 0 or i == len(questions):
            Path(output_file).write_text(json.dumps({
                "summary": {"total": i, "pass": pass_count, "fail": fail_count, "error": error_count},
                "results": results,
            }, indent=2, ensure_ascii=False))

        # Throttle: 2 Sek zwischen Tests um Rate-Limits zu schonen
        time.sleep(2)

    print(f"\n=== FINAL ===\n  Total: {len(questions)}, Pass: {pass_count}, Fail: {fail_count}, Error: {error_count}")
    print(f"  Pass-Rate: {100*pass_count/len(questions):.1f}%")
    print(f"  Saved to {output_file}")


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--limit", type=int, default=None, help="nur erste N Fragen testen")
    p.add_argument("--input", default="tests/genai_questions.yaml")
    p.add_argument("--output", default="tests/genai_results.json")
    args = p.parse_args()
    run(args.input, args.output, args.limit)
