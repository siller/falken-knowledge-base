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

**Qualität**: 20/20 = **100 % Pass-Rate** im Stress-Test über alle Frage-Typen (Schnitt 45 s/Frage).

## Was steht in der Datenbank?

- **8.290 Spiele** (DEL2 13/14 → 22/23 + Oberliga Süd 23/24 → 25/26 inkl. Playoffs)
- **48 Saisons** zurück bis 1980/81 (Rumpf-Tabellenstände + Trainer)
- **194 Spieler** mit Stats für 320 Saison-Einträge
- **58 Trainer-Tenures** (34 unterschiedliche Trainer)
- **45 Playoff-Serien** mit Round + Wins-Verhältnis + Sieger
- **22 News-Artikel** vom RSS-Feed `heilbronner-falken.de` (mit semantischer Suche)
- **Live-Web-Recherche** via Tavily für Externe-Welt-Fragen

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

## Roadmap-Vorschläge

| Idee | Aufwand | Mehrwert |
|---|---|---|
| Mehr News-Quellen (stimme.de, echo24.de) | mittel | bessere News-Antworten |
| Goalie-Stats vollständig (aktuell: 8 Einträge) | mittel | "Wer war bester Torhüter?" |
| Speed-Optimierung (Streaming + Caching) | mittel | gefühlte Reaktionszeit 2× besser |
| Falken-App-Integration (Webview) | gering | direkt in App-Menu |
| Voice-Input | hoch | Mobile-Friendly |
