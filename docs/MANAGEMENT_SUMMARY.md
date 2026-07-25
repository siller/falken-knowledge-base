# HORST — Management Summary

**HORST** (Heilbronner ORakel SporT-AI) ist die GenAI-Wissensdatenbank für die Heilbronner Falken. Live unter [falken-knowledge-base.streamlit.app](https://falken-knowledge-base.streamlit.app), passwortgeschützt für das Team.

## Was kann HORST?

| Frage-Typ | Beispiel | Antwortzeit |
|---|---|---|
| **Saisons + Stats** | "Auf welchem Tabellenplatz beendeten die Falken 2022/23?" | ~30 s |
| **Spieler-Stats** | "Wer war Topscorer 2024/25?" | ~30 s |
| **Trainer** | "Wer war Trainer 2018/19?" | ~40 s |
| **Spielergebnisse** | "Wie endete Memmingen vs Falken am 27.02.2026?" | ~60 s |
| **Playoff-Serien** | "Wer gewann die HF-Serie 2024/25?" | ~70 s |
| **News + Personen** | "Wer ist Steffen Ziesche?" | ~70 s |
| **Web-Recherche** | "Wann hat der Tenno-Sushi-Besitzer bei Falken gespielt?" | ~60 s |

**Qualität** (Stand 25.07.2026): **96,7 %** über die 211 Fragen der Testsuite
(Mai: 91,9 %), 20/20 im Stress-Test über alle Frage-Typen. Antwortzeit aktuell
**5–10 s** pro Frage statt der früher dokumentierten 30–45 s.

## Was steht in der Datenbank? (Stand 25.07.2026)

- **8.867 Spiele** (DEL2 13/14 → 22/23 + Oberliga Süd 23/24 → 25/26 inkl. Playoffs,
  dazu der komplette Spielplan 2026/27)
- **49 Saisons** zurück bis 1980/81 (Rumpf-Tabellenstände + Trainer)
- **244 Spieler** mit Stats für 349 Saison-Einträge, inkl. Kader 2026/27
- **61 Trainer-Amtszeiten** (36 unterschiedliche Trainer, aktuell Jason O'Leary)
- **68 Playoff-Serien** mit Round + Wins-Verhältnis + Sieger
- **131 News-Artikel** aus **10 Quellen** (Vereins-RSS + Lokalpresse über Tavily),
  mit semantischer Suche
- **Live-Web-Recherche** via Tavily für Externe-Welt-Fragen

## Die Saison 2025/26 in der Datenbank

Die Falken beendeten die Oberliga Süd auf **Platz 5** (93 Punkte aus 52 Spielen).
An den Playoffs nahmen sie nach dem **Insolvenzantrag im Januar 2026** nicht teil;
die Saison endete am 27.02.2026. Oberliga-Meister wurden die ECDC Memmingen Indians
(4:2 im Finale gegen Deggendorf). Im Juli 2026 erhielt der Klub die Lizenz für
2026/27 ohne Auflagen und startet am **18.09.2026 in Deggendorf** in die neue Saison.

## Was macht HORST besonders?

1. **Eigene Daten + AI-Synthese**: keine ChatGPT-Halluzinationen — Antworten kommen aus der vereins-eigenen DB
2. **Self-Hosted-LLM**: nutzt DGX-Gemma auf `siller.io`, keine Cloud-Abhängigkeit für die Sprachmodell-Komponente
3. **Multi-Hop-Recherche**: kombiniert Web-Suche + DB-Cross-Lookup für komplexe Fragen
4. **Falken-Branding**: UI im offiziellen Vereins-Look (rot/navy auf hell)
5. **Multi-Turn-Chat**: Folgefragen verstehen Kontext der vorherigen Antwort

## Kosten

| Komponente | Kosten/Monat |
|---|---|
| DGX-LLM | inklusive (eigener Server) |
| Supabase self-hosted | inklusive (eigener Server) |
| **Tavily Web-Search** | **0 €** (1.000 Calls/Monat Free-Tier) |
| **Streamlit Cloud Hosting** | **0 €** (Public-Tier) |
| Tavily over Limit | $0,008/Call (= $8 pro 1.000) |

**Realistisch**: 0 € pro Monat. Tavily Free-Tier reicht bei normalem Team-Use.

## Betrieb

Ein **täglicher GitHub-Actions-Job** (`.github/workflows/sync.yml`) holt News und
Spielergebnisse nach und hält die Streamlit-App wach. Vorher lief jeder Load von
Hand — die Datenbank war deshalb zwischen März und Juli 2026 unbemerkt eingefroren.

## Roadmap-Vorschläge

| Idee | Aufwand | Mehrwert |
|---|---|---|
| Torhüter-Historie vor 2023/24 | mittel | GAA/Sv% auch für die DEL2-Jahre — hockeydata deckt nur die Oberliga ab |
| Speed-Optimierung (Streaming + Caching) | mittel | gefühlte Reaktionszeit 2× besser |
| Falken-App-Integration (Webview) | gering | direkt in App-Menu |
| Auf-/Abstiege als eigenes Feld | gering | "Wann stiegen die Falken ab?" ohne Umweg über Ligawechsel |
| Voice-Input | hoch | Mobile-Friendly |
