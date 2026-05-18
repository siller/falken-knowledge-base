# Datenquellen-Übersicht

Welche Daten wir woher haben, wie viel, wie alt, wie reliable.

## Strukturierte Datenquellen

| Quelle | Was | Saisons | DB-Tabellen | ToS-Status |
|---|---|---|---|---|
| **hockeydata API** (DEB-Key `3c5a99…` + Referer `deb-online.live`) | Oberliga Süd aktuelle Saison: alle Spiele, Tabelle, Spielprotokolle (16 Top-Level-Keys pro Spiel) | nur 2025/26 lieferbar (Oberliga divisionId 18655) | seasons, teams, team_seasons, games, articles | öffentlich bekannt, autorisiert |
| **del-2.org** (HTML-Scrape) | KOMPLETTE DEL2-Historie 2007–2026: Hauptrunden, Playoffs, Playdowns, Testspiele, Cups | 83 Rounds × 19 Saisons | seasons, teams, games | Cache + Rate-Limit 2.5s |
| **EliteProspects** (HTML-Scrape) | Per-Player-Stats pro Saison (GP, G, A, P, PIM, +/-, Position) | 10 Falken-Saisons 2015/16–2024/25 | players, player_seasons, player_stats | aggressives Anti-Scraping, höflicher Scrape mit ~5s Delay funktioniert |
| **eishockey-statistiken.de** (HTML-Scrape) | Falken-Saison-Historie zurück bis 1980/81: Liga, Platzierung, Punkte, Trainer, Tore, Zuschauer, Playoff-Paarungen mit Sp1..Sp7-Einzelergebnissen | 43 Saisons | seasons, team_seasons, coaches, coach_tenures, playoff_series, games (Playoff-Einzelspiele) | hobbyistisch, höflicher Scrape OK |
| **Wikipedia** (MediaWiki API) | DEL2-Saison-Artikel als Narrative für RAG | 10 Saisons (2014/15–2023/24) | articles (mit pgvector-Embeddings) | offizielle API, kein Scraping |

## Nicht (mehr) erschlossen

| Quelle | Grund |
|---|---|
| **rodi-db.de** | URL-Pattern hat sich geändert, alle `team_id`-/`club_id`-Patterns liefern jetzt 404-mit-Footer. Wäre nur Cross-Reference zu EP gewesen — redundant. |
| **hockeydata-API DEL2-historische divisionIds** | Sub-Divisions sind nicht über deb-online.live exposed, Probing zu langsam. del-2.org liefert mehr. |
| **stimme.de / echo24.de** (lokale News) | RSS-Watcher in Phase-1-Erweiterung geplant — heute nicht geladen. |
| **heilbronner-falken.de News** | Dito, RSS-Watcher Phase-1-Erweiterung. |

## Reliability-Hierarchie bei Diskrepanzen

Wenn Quellen sich widersprechen (z.B. unterschiedliche Punkte für eine Saison):

1. **hockeydata-API** (offizielle DEL2/Oberliga-Stats) — höchste Priorität
2. **del-2.org** (offizielle Liga-Website) — sehr verlässlich
3. **eishockey-statistiken.de** (Hobbyist, aber pflichtbewusst) — selten falsch, aber zb. veraltete Punkte-System-Annahmen
4. **EliteProspects** (kommerziell, aber crowd-sourced) — manchmal fehlt +/- bei älteren Saisons
5. **Wikipedia** — narrative Quelle, Zahlen nicht primär nutzen

Im Loader manifestiert sich diese Hierarchie durch die Aufruf-Reihenfolge: spätere Loader überschreiben frühere (COALESCE-Pattern beim Upsert) NUR wenn der spätere Wert non-NULL ist.

## Bekannte Limitierungen

- **EliteProspects Goalie-Stats fehlen** — die Goalie-Tabelle ist auf einer separaten URL, noch nicht erschlossen
- **del-2.org Spiel-Datum-Genauigkeit ist Tagesgenauigkeit** (Uhrzeit ist meist 19:30 Default, weil nicht alle Spiele Anstoßzeit-Angabe haben)
- **Playoff-Spielreihenfolge in Heim/Auswärts** ist eine Heuristik (Sp1 = team_a@home, Sp2 = team_b@home, ...) — manche Serien starten anders
- **eishockey-statistiken Punkte vor 1997/98** sind NULL, weil das alte Punktesystem (2-1-0 statt 3-2-1-0) nicht ausgewiesen ist

## Cache-Strategie

Alle gescrapten Seiten landen in `cache/{source}/{url_hash}.html`. Bei Schema-Iterationen
kann der Loader gegen den Cache re-parsen, ohne erneut zu fetchen. Cache ist
permanent; manuelles Löschen für Force-Refresh.
