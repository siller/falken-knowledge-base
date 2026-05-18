"""Erzeugt eine schöne Markdown-Datei aus genai_results JSON.

Aufruf: python3 scripts/render_results_md.py <input.json> <output.md>
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def render(input_path: Path, output_path: Path, title: str = "GenAI Test-Ergebnisse") -> None:
    data = json.loads(input_path.read_text())
    summary = data.get("summary", {})
    results = data.get("results", [])

    total = summary.get("total", len(results))
    p = summary.get("pass", sum(1 for r in results if r.get("pass")))
    f = summary.get("fail", sum(1 for r in results if not r.get("pass") and "error" not in r))
    e = summary.get("error", sum(1 for r in results if "error" in r))
    rate = 100.0 * p / total if total else 0

    lines: list[str] = []
    lines.append(f"# {title}")
    lines.append("")
    lines.append(f"**Quelle:** `{input_path.name}`")
    lines.append("")
    lines.append(f"## Zusammenfassung")
    lines.append("")
    lines.append(f"| Metrik | Wert |")
    lines.append(f"|---|---|")
    lines.append(f"| Tests gesamt | **{total}** |")
    lines.append(f"| ✓ Pass | **{p}** |")
    lines.append(f"| ✗ Fail | {f} |")
    lines.append(f"| 💥 Error | {e} |")
    lines.append(f"| Pass-Rate | **{rate:.1f} %** |")
    lines.append("")

    # Per category
    by_cat = defaultdict(lambda: {"pass": 0, "fail": 0, "error": 0})
    for r in results:
        c = r.get("category", "?")
        if "error" in r:
            by_cat[c]["error"] += 1
        elif r.get("pass"):
            by_cat[c]["pass"] += 1
        else:
            by_cat[c]["fail"] += 1

    lines.append("## Pass-Rate pro Kategorie")
    lines.append("")
    lines.append("| Kategorie | Pass | Fail | Error | Pass-Rate |")
    lines.append("|---|---:|---:|---:|---:|")
    for cat in sorted(by_cat, key=lambda c: -(by_cat[c]["pass"] + by_cat[c]["fail"])):
        d = by_cat[cat]
        t = d["pass"] + d["fail"] + d["error"]
        rate_c = 100.0 * d["pass"] / t if t else 0
        lines.append(f"| {cat} | {d['pass']} | {d['fail']} | {d['error']} | {rate_c:.0f} % |")
    lines.append("")

    # Per result
    lines.append("## Einzelergebnisse")
    lines.append("")
    for r in results:
        marker = "💥" if "error" in r else ("✓" if r.get("pass") else "✗")
        idx = r.get("id", "?")
        cat = r.get("category", "?")
        q = (r.get("question", "") or "").replace("\n", " ")
        expected = r.get("expected_facts", [])
        answer = (r.get("actual_answer", "") or "").replace("\n", " ")
        sql = (r.get("sql", "") or "").strip().replace("\n", " ")
        err = r.get("error", "") or ""
        t_sec = r.get("time_sec", "?")

        lines.append(f"### {marker} `{idx}` ({cat}, {t_sec}s)")
        lines.append("")
        lines.append(f"**Frage:** {q}")
        lines.append("")
        lines.append(f"**Erwartet:** `{expected}`")
        lines.append("")
        if err:
            lines.append(f"**Fehler:** `{err[:300]}`")
        elif answer:
            lines.append(f"**Antwort:** {answer}")
        else:
            lines.append(f"**Antwort:** _(leer)_")
        lines.append("")
        if sql:
            sql_display = sql[:600] + ("..." if len(sql) > 600 else "")
            lines.append(f"```sql")
            lines.append(sql_display)
            lines.append(f"```")
            lines.append("")
        if not r.get("pass") and "error" not in r:
            missing = r.get("missing_facts", [])
            if missing:
                lines.append(f"**Fehlende Fakten:** `{missing}`")
                lines.append("")
        lines.append("---")
        lines.append("")

    output_path.write_text("\n".join(lines))
    print(f"Geschrieben: {output_path} ({output_path.stat().st_size:,} Bytes)")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: render_results_md.py <input.json> <output.md> [<title>]")
        sys.exit(1)
    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])
    title = sys.argv[3] if len(sys.argv) > 3 else "GenAI Test-Ergebnisse"
    render(inp, out, title)
