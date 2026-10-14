# Fix: Laufende Saison bleibt in der Wissensbasis leer

**Datum:** 15.10.2026 · **Branch:** `fix/laufende-saison-sync` · **Anlass:** HORST nennt auf
„Wer ist der aktuelle Topscorer?“ Calder Anderson (68 Punkte, 2025/26). Für 2026/27 findet er nichts.

## Diagnose (belegt)

Stand Supabase am 15.10.2026 für 2026/27: 370 Spiele, davon **0 mit Ergebnis** (69 liegen in der Vergangenheit),
Falken-Zeile in `team_seasons` mit `games_played = 0`, 18 Kaderspieler **ohne Statistik**.
hockeydata (Division 21614) liefert dagegen 63 beendete Partien, die Falken mit 9 Spielen und 18 Punkten
und Topscorer Frederik Cabana mit 17 Punkten.

1. **`falken.upsert_game` fügt nur ein** (`INSERT … WHERE NOT EXISTS hockeydata-ID`). Der Spielplan kam am
   31.07. ohne Ergebnisse, danach überspringt jeder Lauf die bekannten Partien.
2. **Team-Alias zerstört die Falken-Tabellenzeile.** hockeydata nennt den Klub „Heilbronner EC Falken“ (teamId 70543).
   `upsert_team` legt dafür täglich ein neues Team an, `upsert_team_season` schreibt dorthin.
   `merge_known_duplicates` → `dedup.merge_teams` löscht bei einem Konflikt die neue Zeile und behält die alte mit 0 Spielen.
3. **Spielerstatistiken der laufenden Saison lädt niemand.** `get_leader_field_players` ist vorhanden, wird aber nicht aufgerufen.
   Der EliteProspects-Loader hat den Kader 2026/27 bewusst ohne Zahlen angelegt.
4. **Der Sync läuft seit dem 08.10. nicht mehr.** GitHub hat den Workflow nach 60 Tagen ohne Commit abgeschaltet
   (`disabled_inactivity`). Vorher war er jeden Tag grün, obwohl `letztes_ergebnis` auf dem 01.05.2026 stand.

Folge in HORST: „aktuelle Saison“ ist `max(season) … WHERE games_played > 0` (`fact_sql.py`). Ergebnis ist 2025/26 und damit Anderson.

## Umsetzung (ohne SQL-Migration)

Migrationen gehen nur von Hand über das Studio, deshalb läuft alles über die vorhandenen REST-Tabellen und RPCs.

- [ ] `loaders.upsert_games_from_schedule`: nach dem RPC Termin, Ergebnis und OT/SO der bekannten Partie per
  `falken_games.update` nachtragen, über `source_ids->>hockeydata`. Angesetzte Partien (`gameStatus 0`) überschreiben nie ein Ergebnis.
- [ ] `loaders.upsert_team`: Namen über `falken_teams.alt_names` auf das kanonische Team auflösen.
- [ ] `loaders.upsert_skater_stats_from_leaders` + `falken_team_ids`: LeaderFieldPlayers der Falken nach
  `player_stats`. Abgleich ohne Akzente und Groß-/Kleinschreibung erst gegen den Saisonkader, dann gegen alle
  Spieler, sonst neu anlegen.
- [ ] `sync_daily.py`: neuer Schritt „Spielerstatistik“. Der Aktualitätsbericht wird rot bei mehr als 3 offenen
  Ligaergebnissen, die älter als 2 Tage sind, oder wenn die Falken-Zeile mehr als 2 Spiele hinter der Liga liegt.
- [ ] `sync.yml`: Keepalive über die API `PUT …/workflows/sync.yml/enable` (`permissions: actions: write`).
- [ ] `fact_sql.py`: Topscorer-Beispiel für die aktuelle Saison mit `season` in der Ausgabe. Die Synthese nennt
  die Saison immer, damit kein Vorsaison-Wert als „aktuell“ durchgeht.

Tests: `tests/test_laufende_saison_sync.py` (Fake-PostgREST, keine echte DB).

## Rollout (nur nach OK)

1. PR → `main` mergen (die Action nutzt `main`).
2. Workflow wieder einschalten: `gh workflow enable sync.yml`, dann `gh workflow run sync.yml`.
3. Danach in Supabase prüfen: Ergebnisse 2026/27, Falken-Zeile, `falken_skater_stats` 2026/27.
4. horst-api neu bauen und ausrollen (Prompt-Änderung), dann gegen `/frage` nachmessen.
