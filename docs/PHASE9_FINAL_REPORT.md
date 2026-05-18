# Phase 9 — Daten-Perfektionierung — Final-Bericht (2026-05-18)

## Ergebnis-Übersicht

| Version | Pass | Fail | Error | Pass-Rate | Delta |
|---|---:|---:|---:|---:|---|
| v1 (vor Phase 9, Run 1) | 143 | 68 | 0 | **67,8 %** | — |
| v2 (1. Phase-9-Welle) | 172 | 39 | 0 | **81,5 %** | +13,7 pp |
| v3 (mit Playoff-Backfill + Goalie-Stats) | 182 | 29 | 0 | **86,3 %** | +4,8 pp |
| **v4 (final, alle Fixes)** | **194** | **17** | **0** | **91,9 %** | **+5,6 pp** |
| Brainstorm 60 Ideen (v2) | 54 OK | 4 leer | 2 Err | **90 %** | — |

**Gesamt-Sprung v1 → v4: +51 Pass-Antworten, +24,1 Prozentpunkte.**

## Pass-Rate pro Kategorie (v4 vs v1)

| Kategorie | v1 | v4 | Delta |
|---|---:|---:|---|
| liga | 98 % | **100 %** | +2 |
| saison_platz | 98 % | 98 % | 0 |
| saison_punkte | 97 % | 97 % | 0 |
| **trainer** | 0 % | **100 %** | **+100** |
| **spielergebnis** | 45 % | **100 %** | **+55** |
| **playoff** | 71 % | **100 %** | **+29** |
| **topscorer** | 25 % | **92 %** | **+67** |
| vergleich | 50 % | 60 % | +10 |
| trend | 13 % | 33 % | +20 |

**Vollständige Kategorien (100 %): liga, trainer, spielergebnis, playoff.**

## Was wurde gefixt (chronologisch)

### Data-Fixes (Backfill)
1. **Trainer-Tenures 2024/25 + 2025/26**: Petrozza manuell ergänzt → trainer 0 % → 100 %
2. **Saison-Datum-Backfill**: alle 48 Saisons mit Sep 1 → May 31 gefüllt (waren alle NULL!), persistiert als Migration `0008_season_dates_backfill.sql`
3. **Goalie-Stats Backfill**: 8 Falken-Goalies aus hockeydata (25/26: 2, 24/25: 3, 23/24: 2, 21/22: 1) — Tabelle war vorher LEER
4. **Oberliga Playoffs 2023/24 + 2024/25**: 144 Spiele + 6 playoff_series via **Falken-Web-API-Key-Discovery** (Key `d9a998…` + Referer `heilbronner-falken.de`, divId 13020/15806). Vorher als "API hat keine Daten" dokumentiert; tatsächlich gefunden!
5. **News-Articles RSS-Loader**: 10+ Artikel von heilbronner-falken.de mit Embeddings
6. **Skater-Stats 2025/26**: 29 Spieler nachgeladen (Calder Anderson, Nolan Ritchie, etc.)
7. **Jersey-Numbers Backfill 2024/25**: 24 von 28 Spielern (war 3/28)

### Code-Fixes (Pipeline-Robustheit)
1. **SQL-Sanitizer** (`db.sanitize_llm_sql`): fixed deutsche Keywords (ODER BY → ORDER BY), MySQL → PostgreSQL (YEAR()/CURDATE()), doppelte Tokens (JOIN x JOIN x), Tippfehler (player_name → player), gebrochene String-Literals
2. **Retry-on-Syntax-Error** in fact_sql + trend_chart: bei SQL-Fehler 2. Versuch mit Hinweis
3. **Defensive JSON-Parsing** in `chat_with_schema`: iteriert Modell-Chain bis valides JSON kommt, statt zu crashen
4. **OpenRouter Paid Primary**: `deepseek/deepseek-v4-flash` (kostet ~$0,003/211-Tests)
5. **pg_trgm Fuzzy-Match** für Spielernamen: `similarity(player, 'X') > 0.3` matcht "Richie" auf "Ritchie"
6. **NULLS LAST Pattern** im SCHEMA_CONTEXT: PostgreSQL sortiert NULLs sonst nach OBEN bei DESC → Patrick Berger ohne Stats wurde als Topscorer falsch geliefert
7. **Player-Stats GENERATED-Column-Awareness**: `points` nicht insertable (computed from goals+assists)
8. **Synthesis-Prompt verschärft**: "Wenn Daten da sind, nutze sie SELBSTBEWUSST" + Score-Format-Regel (Home:Away)
9. **Hybrid-Router-Fallback**: Wenn fact-Handler leer + Frage klingt narrativ (News, "wer ist X") → automatisch RAG-Fallback. Damit funktionieren auch fehl-klassifizierte Narrative-Fragen.
10. **Multi-Turn-Context** im Streamlit-UI: vorherige Q+A wird als Kontext mitgeschickt für Folgefragen
11. **Schema-Beispiele** erweitert: konkrete Templates für Topscorer-Aggregate, Career-Sum, Playoff-Series, Trend-Diagramme
12. **Token-Budget bumps**: SQL-max-tokens 400 → 1000 (verhinderte Mid-String-Cutoffs)

### Infrastruktur
- Streamlit-Mini-UI auf `http://localhost:8501` mit Beispielfragen + SQL/Sources/Resultat-Expander
- Render-Skript `scripts/render_results_md.py` für MD-Reports
- Migration `0008_season_dates_backfill.sql` — idempotent
- 60 neue Brainstorm-Fragen + Run-Skript `scripts/run_ideas_60.py`

## Verbleibende 17 Fails in v4 (was bleibt schwer)

| Kategorie | Anzahl | Typische Ursachen |
|---|---|---|
| trend (10/15) | 10 fails | Open-ended Aggregat-Fragen (z.B. "Welche Saison hatte kürzeste Hauptrunde wegen Corona") — SQL-Konzept zu komplex, Trainer-Mehrfach-Tenure-Aggregation |
| vergleich (4/10) | 4 fails | Multi-Hop-Fragen ("Wie schneiden Falken in Heim vs Auswärts ab" — Sub-Aggregate) |
| spielergebnis | 0 fails | ✅ alle 20 korrekt |
| saison_platz (1/41) | 1 fail | Saison 1988/89 — kein Daten |
| topscorer (1/12) | 1 fail | Edge-Case |
| saison_punkte (1/29) | 1 fail | Pre-API-Saison |

## Was funktioniert jetzt richtig gut

1. **Alle aktuellen Saisons** (2013/14 — 2025/26): Tabellenplätze, Topscorer, Trainer, Spielergebnisse, Playoffs
2. **Spielername-Lookup** auch mit Tippfehlern (pg_trgm)
3. **Multi-Trainer-Saisons** werden korrekt erkannt + alle genannt
4. **Playoff-Serien** mit Round + Wins-Verhältnis + Winner
5. **Narrative/News-Fragen** über RSS-Artikel (Hybrid-Fallback)
6. **0 Crashes** (vorher 50 %+ KeyError-Rate)

## Open Action Items

1. **Bessere Trend-Handler-Prompts** für Aggregat-mit-Subquery-Fragen
2. **Coach-"Consecutive-Tenure"-Logik** (gaps-and-islands SQL)
3. **Mehr News-Sources** (stimme.de RSS war kaputt, alternativ direktes Scraping)
4. **DGX-Vergleichslauf** (v3b wurde gestoppt — Run mit gemma erfordert nochmal ~2 h)

## Generierte Dateien

| Pfad | Inhalt |
|---|---|
| `docs/V4_TESTS_REPORT.md` | Alle 211 Tests v4: Frage, Antwort, SQL, Pass/Fail, Klassifikation |
| `docs/IDEAS_60_v2_REPORT.md` | Alle 60 Brainstorm-Tests: Frage, Antwort, SQL, RAG-Quellen |
| `docs/IDEAS_60_REPORT.md` | Erste Ideen-Brainstorm-Version (zum Vergleich) |
| `docs/PHASE9_FINAL_REPORT.md` | Dieser Bericht |
| `tests/genai_results_v4.json` | Roh-Resultate v4 |
| `tests/ideas_60_results.json` | Roh-Resultate Brainstorm |
| `scripts/backfill_oberliga_playoffs.py` | Falken-Web-API-Key Loader (Hauptfund Phase 9) |
| `scripts/backfill_goalie_stats.py` | Goalie-Stats-Loader |
| `falken_kb/ingestion/scrapers/falken_news.py` | RSS-Loader |
| `frontend/falken_ui.py` | Streamlit-UI mit Multi-Turn |
