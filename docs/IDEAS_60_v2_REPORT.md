# 60 Brainstorm-Tests v2 (mit Hybrid-RAG-Fallback + Jersey-Daten-Backfill)

**Quelle:** `tests/ideas_60_results.json`  ·  **Datum:** 2026-05-18 abend

## Zusammenfassung

| Metrik | Wert |
|---|---|
| Tests gesamt | **60** |
| Brauchbare Antworten | **54** (90 %) |
| Leere | 4 |
| SQL-Fehler | 2 |

## Per Kategorie

| Kategorie | OK | Empty | Err |
|---|---:|---:|---:|
| edge | 5 | 0 | 0 |
| goalie | 4 | 0 | 0 |
| liga | 2 | 0 | 1 |
| narrative | 4 | 0 | 0 |
| out_of_scope | 4 | 0 | 0 |
| playoff | 5 | 0 | 0 |
| saison_platz | 1 | 0 | 0 |
| saison_punkte | 1 | 0 | 0 |
| spieler | 5 | 2 | 1 |
| spielergebnis | 5 | 1 | 0 |
| topscorer | 1 | 0 | 0 |
| trainer | 5 | 0 | 0 |
| trend | 7 | 1 | 0 |
| vergleich | 5 | 0 | 0 |

## Einzelergebnisse

### 💥 `idea_001` — liga (10.2s)

**Frage:** In welcher Liga spielen die Heilbronner Falken aktuell?

**Antwort:** ⚠️  Konnte die Frage nicht beantworten (SQL-Fehler: {'code': '42P10', 'details': None, 'hint': None, 'message': 'for SELECT DISTINCT, ORDER BY expressions must appear in select list'}).

```sql
SELECT DISTINCT s.league FROM seasons s JOIN team_seasons ts ON ts.season_id = s.id JOIN teams t ON t.id = ts.team_id WHERE t.name = 'Heilbronner Falken' ORDER BY s.start_date DESC LIMIT 1;
```

---

### ✓ `idea_002` — saison_platz (10.4s)

**Frage:** Wo standen die Falken am Ende der Hauptrunde 2025/26?

**Antwort:** Die Falken belegten am Ende der Hauptrunde 2025/26 den 5. Platz.

```sql
SELECT final_rank FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2025/26' AND is_focus_team_season = TRUE;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_003` — saison_punkte (29.4s)

**Frage:** Wie viele Punkte hatten die Falken in der gesamten Saisongeschichte zusammen?

**Antwort:** Die Falken hatten in der gesamten Saisongeschichte insgesamt 2199 Punkte.

```sql
SELECT SUM(points) AS total_points FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_004` — liga (20.9s)

**Frage:** Wie lange spielten die Heilbronner Falken in der DEL2 insgesamt?

**Antwort:** Die Heilbronner Falken spielten 9 Jahre in der DEL2, von der ersten Saison am 2013-09-01 bis zur letzten am 2023-05-31, insgesamt also 10 Saisons.

```sql
SELECT COUNT(*) AS total_del2_seasons, MIN(start_date) AS erste_saison, MAX(end_date) AS letzte_saison, EXTRACT(YEAR FROM AGE(MAX(end_date), MIN(start_date))) AS jahre FROM seasons s WHERE s.id IN (SELECT season_id FROM team_seasons ts JOIN teams t ON t.id = ts.team_id AND t.name = 'Heilbronner Falken' WHERE ts.season_id IN (SELECT id FROM seasons WHERE league = 'DEL2'))
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_005` — liga (49.1s)

**Frage:** Wann sind die Falken aus der DEL2 abgestiegen?

**Antwort:** Die Heilbronner Falken sind in der Saison 2022/23 aus der DEL2 abgestiegen.

```sql
SELECT season FROM season_standings WHERE team = 'Heilbronner Falken' AND league = 'DEL2' AND final_rank = 12 ORDER BY season DESC LIMIT 1
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_006` — trainer (18.0s)

**Frage:** Wer ist aktuell Trainer der Falken?

**Antwort:** Francesco Petrozza ist aktuell Headcoach der Falken.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date
FROM coach_tenures ct
JOIN coaches c ON c.id = ct.coach_id
JOIN teams t ON t.id = ct.team_id
JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date
WHERE t.name = 'Heilbronner Falken' AND s.label = '2024/25' AND ct.role = 'Headcoach'
ORDER BY ct.start_date DESC LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_007` — topscorer (12.2s)

**Frage:** Wer ist aktueller Topscorer der Falken?

**Antwort:** Calder ANDERSON ist mit 68 Punkten (30 Tore, 38 Assists) aktueller Topscorer der Falken.

```sql
SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = (SELECT MAX(season) FROM falken_skater_stats) AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_008` — spielergebnis (21.4s)

**Frage:** Was war das letzte Heimspiel der Falken?

**Antwort:** Das letzte Heimspiel der Falken war am 22. Februar 2026 gegen die Erding Gladiators, das sie mit 2:7 verloren.

```sql
SELECT g.date, ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE ht.name = 'Heilbronner Falken' ORDER BY g.date DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_009` — vergleich (42.2s)

**Frage:** Wie viele Siege haben die Falken in der aktuellen Saison?

**Antwort:** Die Falken haben in der aktuellen Saison 2025/26 insgesamt 27 Siege erzielt.

```sql
SELECT season, wins FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE ORDER BY season DESC LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_010` — vergleich (114.4s)

**Frage:** Wie viele Tore haben die Falken in der laufenden Saison erzielt?

**Antwort:** Die Falken haben in der laufenden Saison 208 Tore erzielt.

```sql
SELECT goals_for FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE ORDER BY season DESC LIMIT 1
```

_DB-Resultat: 1 Zeile(n)_

---

### 💥 `idea_011` — spieler (11.9s)

**Frage:** Wie viele Saisons spielte Nolan Ritchie für die Falken?

**Antwort:** ⚠️  Konnte die Frage nicht beantworten (SQL-Fehler: {'code': '42601', 'details': None, 'hint': None, 'message': 'syntax error at or near "FROM"'}).

```sql
SELECT COUNT(DISTINCT season FROM falken_skater_stats WHERE similarity(player, 'Nolan Ritchie') > 0.3
```

---

### ✓ `idea_012` — spieler (17.9s)

**Frage:** Was war die beste Saison von Dylan Wruck punktemäßig?

**Antwort:** Die beste Saison von Dylan Wruck punktemäßig war die Saison 2019/20 mit 88 Punkten (24 Tore und 64 Assists).

```sql
SELECT season, points, goals, assists FROM falken_skater_stats WHERE similarity(player, 'Dylan Wruck') > 0.3 AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_013` — spieler (10.1s)

**Frage:** Hat Dylan Wruck mehr als 200 Karriere-Punkte für die Falken?

**Antwort:** Nein, Dylan Wruck hat für die Falken nur 166 Karriere-Punkte erzielt, also weniger als 200.

```sql
SELECT SUM(points) AS career_points FROM falken_skater_stats WHERE similarity(player, 'Dylan Wruck') > 0.3 AND points IS NOT NULL
```

_DB-Resultat: 1 Zeile(n)_

---

### ⚠️ `idea_014` — spieler (18.8s)

**Frage:** Welche Nationalität hatte Robert Hock?

**Antwort:** _(leer)_

```sql
SELECT nation FROM players WHERE similarity(name, 'Robert Hock') > 0.3 ORDER BY similarity(name, 'Robert Hock') DESC LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_015` — spieler (24.4s)

**Frage:** Wer trug das Trikot mit Nummer 10 in der Saison 2024/25?

**Antwort:** Nolan Ritchie trug in der Saison 2024/25 das Trikot mit der Nummer 10.

```sql
SELECT player, jersey_number FROM falken_skater_stats WHERE season = '2024/25' AND jersey_number = 10;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_016` — spieler (8.9s)

**Frage:** Wie viele Tore hat Nolan Ritchie in der Saison 2024/25 erzielt?

**Antwort:** Nolan Ritchie hat in der Saison 2024/25 38 Tore erzielt.

```sql
SELECT season, player, goals FROM falken_skater_stats WHERE similarity(player, 'Nolan Ritchie') > 0.3 AND season = '2024/25' AND goals IS NOT NULL ORDER BY similarity(player, 'Nolan Ritchie') DESC LIMIT 1
```

_DB-Resultat: 1 Zeile(n)_

---

### ⚠️ `idea_017` — spieler (25.8s)

**Frage:** Welche Spieler hatten mehr als 80 Punkte in einer Saison bei den Falken?

**Antwort:** _(leer)_

```sql
SELECT season, player, points, goals, assists FROM falken_skater_stats WHERE points > 80 ORDER BY points DESC NULLS LAST;
```

_DB-Resultat: 5 Zeile(n)_

---

### ✓ `idea_018` — spieler (12.5s)

**Frage:** Hat Calder Anderson in 2025/26 mehr Tore als Vorlagen?

**Antwort:** Nein, Calder Anderson hatte in der Saison 2025/26 mit 30 Toren und 38 Vorlagen mehr Vorlagen als Tore.

```sql
SELECT season, player, goals, assists FROM falken_skater_stats WHERE similarity(player, 'Calder Anderson') > 0.3 AND season = '2025/26' ORDER BY similarity(player, 'Calder Anderson') DESC LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_019` — goalie (10.2s)

**Frage:** Wer war der beste Torhüter der Falken in der Saison 2024/25 nach Gegentor-Schnitt?

**Antwort:** Der beste Torhüter der Heilbronner Falken in der Saison 2024/25 nach Gegentor-Schnitt war Patrick BERGER mit einem GAA von 2,73.

```sql
SELECT goalie, gaa, save_pct, shutouts FROM falken_goalie_stats WHERE season = '2024/25' AND gaa IS NOT NULL ORDER BY gaa ASC NULLS LAST LIMIT 1
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_020` — goalie (24.0s)

**Frage:** Welche Torhüter spielten 2025/26 für die Falken?

**Antwort:** In der Saison 2025/26 spielten Konrad MARKUS (Rückennummer 1) und Julian SCHMITT (Rückennummer 22) als Torhüter für die Falken.

```sql
SELECT goalie, jersey_number, jersey_number, games_played, wins, losses, gaa, save_pct, shutouts FROM falken_goalie_stats WHERE season = '2025/26' ORDER BY games_played DESC NULLS LAST;
```

_DB-Resultat: 2 Zeile(n)_

---

### ✓ `idea_021` — goalie (10.0s)

**Frage:** Wie viele Siege hatte Nico Zimmermann in der Saison 2024/25?

**Antwort:** Nico Zimmermann hatte in der Saison 2024/25 18 Siege.

```sql
SELECT SUM(wins) AS total_wins FROM falken_goalie_stats WHERE similarity(goalie, 'Nico Zimmermann') > 0.3 AND season = '2024/25'
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_022` — goalie (17.9s)

**Frage:** Hatte Michael Paterson-Jones in 24/25 eine bessere Save-Quote als Nico Zimmermann?

**Antwort:** Nein, Michael Paterson-Jones hatte in der Saison 24/25 mit einer Save-Quote von 0,902 keine bessere Quote als Nico Zimmermann, der eine Save-Quote von 0,905 aufwies.

```sql
SELECT goalie, save_pct FROM falken_goalie_stats WHERE season = '2024/25' AND (similarity(goalie, 'Michael Paterson-Jones') > 0.3 OR similarity(goalie, 'Nico Zimmermann') > 0.3) ORDER BY goalie;
```

_DB-Resultat: 2 Zeile(n)_

---

### ✓ `idea_023` — trainer (31.3s)

**Frage:** Wie lange war Rico Rossi Trainer der Falken?

**Antwort:** Rico Rossi sr. war vom 1. September 2004 bis zum 31. Mai 2013 Trainer der Heilbronner Falken, also insgesamt neun Spielzeiten.

```sql
SELECT c.name, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id WHERE t.name = 'Heilbronner Falken' AND ct.role = 'Headcoach' AND similarity(c.name, 'Rico Rossi') > 0.3 ORDER BY similarity(c.name, 'Rico Rossi') DESC;
```

_DB-Resultat: 9 Zeile(n)_

---

### ✓ `idea_024` — trainer (13.6s)

**Frage:** Welcher Trainer hatte die längste durchgehende Amtszeit bei den Falken?

**Antwort:** Georges Hüttig hatte mit 273 Tagen (vom 1. September 1983 bis 31. Mai 1984) die längste durchgehende Amtszeit bei den Falken.

```sql
SELECT c.name, ct.start_date, ct.end_date, (ct.end_date - ct.start_date) AS tenure_days
FROM coach_tenures ct
JOIN coaches c ON c.id = ct.coach_id
JOIN teams t ON t.id = ct.team_id
WHERE t.name = 'Heilbronner Falken' AND ct.role = 'Headcoach'
ORDER BY tenure_days DESC NULLS LAST
LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_025` — trainer (25.6s)

**Frage:** Wer war der erste Trainer der Falken überhaupt?

**Antwort:** Der erste Trainer der Falken war Josef Matousek, der am 1. September 1980 startete.

```sql
SELECT c.name, ct.start_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id WHERE t.name = 'Heilbronner Falken' AND ct.role = 'Headcoach' ORDER BY ct.start_date ASC LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_026` — trainer (13.1s)

**Frage:** Wer war Trainer der Falken in der Klassenerhalt-Saison 2015/16?

**Antwort:** In der Saison 2015/16 waren Manfred Wolf und Fabian Dahlem die Headcoaches der Falken.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2015/16' AND ct.role = 'Headcoach';
```

_DB-Resultat: 2 Zeile(n)_

---

### ✓ `idea_027` — playoff (57.7s)

**Frage:** Wie weit kamen die Falken in den Oberliga-Süd Playoffs 2024/25?

**Antwort:** Die Heilbronner Falken erreichten in den Oberliga-Süd Playoffs 2024/25 das Halbfinale, wo sie mit 2:4 Siegen gegen die Hannover Scorpions ausschieden.

```sql
SELECT ps.round, ta.name AS team_a, tb.name AS team_b, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2024/25' AND s.league = 'Oberliga Süd' AND ('Heilbronner Falken' IN (ta.name, tb.name)) ORDER BY ps.rou...
```

_DB-Resultat: 3 Zeile(n)_

---

### ✓ `idea_028` — playoff (31.3s)

**Frage:** Welche Teams haben die Falken im Viertelfinale 2023/24 besiegt?

**Antwort:** Die Falken haben im Viertelfinale 2023/24 die ECDC Memmingen Indians besiegt.

```sql
SELECT CASE WHEN ps.team_a_id = (SELECT id FROM teams WHERE name = 'Heilbronner Falken') THEN tb.name ELSE ta.name END AS opponent FROM playoff_series ps JOIN seasons s ON s.id = ps.season_id JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id WHERE s.label = '2023/24' AND ps.round = 'Viertelfinale' AND ps.winner_team_id = (SELECT id FROM teams WHERE name = 'Heilbronner Fal...
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_029` — playoff (36.7s)

**Frage:** Wie viele Playoff-Serien haben die Falken in der DEL2-Zeit gewonnen?

**Antwort:** Die Heilbronner Falken haben in der DEL2-Zeit 4 Playoff-Serien gewonnen.

```sql
SELECT COUNT(*) AS series_won FROM playoff_series ps JOIN seasons s ON s.id = ps.season_id JOIN teams t ON t.id = ps.winner_team_id WHERE s.league = 'DEL2' AND t.name = 'Heilbronner Falken';
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_030` — playoff (10.5s)

**Frage:** Welches Team hat die Falken am häufigsten in den Playoffs eliminiert?

**Antwort:** ESV Kaufbeuren hat die Falken am häufigsten in den Playoffs eliminiert, und zwar 2 Mal.

```sql
SELECT t.name, COUNT(*) AS eliminations FROM playoff_series ps JOIN seasons s ON s.id = ps.season_id JOIN teams t ON t.id = ps.winner_team_id WHERE (ps.team_a_id = (SELECT id FROM teams WHERE name = 'Heilbronner Falken') OR ps.team_b_id = (SELECT id FROM teams WHERE name = 'Heilbronner Falken')) AND ps.winner_team_id != (SELECT id FROM teams WHERE name = 'Heilbronner Falken') GROUP BY t.name ORDER...
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_031` — playoff (11.1s)

**Frage:** Wie viele Playdown-Serien spielten die Falken in der DEL2?

**Antwort:** Die Heilbronner Falken bestritten in der DEL2 genau 8 Playdown-Serien.

```sql
SELECT COUNT(*) AS playdown_series_count FROM playoff_series ps JOIN seasons s ON s.id = ps.season_id JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id WHERE s.league = 'DEL2' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ps.round LIKE 'Play-Down%'
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_032` — spielergebnis (24.7s)

**Frage:** Was war das höchste Tor-Ergebnis der Falken in einem einzelnen Spiel?

**Antwort:** Das höchste Tor-Ergebnis der Falken in einem einzelnen Spiel war 12 Tore, erreicht am 2024-10-18: Heilbronner Falken 12:6 SC Riessersee.

```sql
SELECT g.home_score, g.away_score, g.date::date, ht.name AS home_team, at.name AS away_team, (CASE WHEN ht.name = 'Heilbronner Falken' THEN g.home_score ELSE g.away_score END) AS falken_goals FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken') AND (CASE WHEN ht.name = 'Heilbronner Falk...
```

_DB-Resultat: 5 Zeile(n)_

---

### ✓ `idea_033` — spielergebnis (11.1s)

**Frage:** Was war die höchste Niederlage der Falken in einem Spiel?

**Antwort:** Die höchste Niederlage der Heilbronner Falken war am 29. September 2023 ein 12:0 gegen den EV Füssen, wobei die Falken als Heimteam 12 Gegentore kassierten.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, ABS(g.home_score - g.away_score) AS diff, g.date FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE ('Heilbronner Falken' IN (ht.name, at.name)) AND (g.home_score IS NOT NULL AND g.away_score IS NOT NULL) ORDER BY diff DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ⚠️ `idea_034` — spielergebnis (27.3s)

**Frage:** Wie oft haben die Falken in der Saison 2025/26 gegen Memmingen gespielt und mit welchen Ergebnissen?

**Antwort:** _(leer)_

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout, g.date FROM games g JOIN seasons s ON s.id = g.season_id JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE s.label = '2025/26' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('ECDC Memmingen Indians' IN (ht.name, at.name)) ORDER BY g.date;
```

_DB-Resultat: 4 Zeile(n)_

---

### ✓ `idea_035` — spielergebnis (7.4s)

**Frage:** Wie viele Spiele endeten in der Saison 2024/25 in Overtime?

**Antwort:** 55 Spiele endeten in der Saison 2024/25 in Overtime.

```sql
SELECT COUNT(*) AS overtime_games FROM games g JOIN seasons s ON s.id = g.season_id WHERE s.label = '2024/25' AND g.overtime = TRUE;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_036` — spielergebnis (17.3s)

**Frage:** Welches Spiel hatte die meisten Gesamttore in der Saison 2023/24?

**Antwort:** Das Spiel mit den meisten Gesamttoren in der Saison 2023/24 war **ECDC Memmingen Indians 7:6 Heilbronner Falken** mit insgesamt 13 Toren.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, (g.home_score + g.away_score) AS total_goals FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id JOIN seasons s ON s.id = g.season_id WHERE s.label = '2023/24' AND ('Heilbronner Falken' IN (ht.name, at.name)) ORDER BY total_goals DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_037` — trend (23.4s)

**Frage:** In welcher Saison hatten die Falken die meisten Tore?

**Antwort:** In der Saison 1986/87 erzielten die Falken mit 296 Toren die meisten Treffer.

```sql
SELECT season, goals_for FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE AND goals_for IS NOT NULL ORDER BY goals_for DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_038` — trend (10.2s)

**Frage:** Welcher Spieler hat in der Falken-Geschichte die meisten Karriere-Tore?

**Antwort:** Justin Kirsch hat in der Falken-Geschichte mit 139 Toren die meisten Karriere-Tore erzielt.

```sql
SELECT player, SUM(goals) AS total_goals FROM falken_skater_stats WHERE goals IS NOT NULL GROUP BY player ORDER BY total_goals DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ⚠️ `idea_039` — trend (41.4s)

**Frage:** Wie hat sich die Tordifferenz der Falken in den letzten 5 Saisons entwickelt?

**Antwort:** _(leer)_

```sql
SELECT season AS x, goal_diff AS y FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE AND goal_diff IS NOT NULL AND season >= '2018/19' ORDER BY season ASC
```

_DB-Resultat: 8 Zeile(n)_

---

### ✓ `idea_040` — trend (39.9s)

**Frage:** Wie viele unterschiedliche Spieler trugen je das Falken-Trikot?

**Antwort:** 230 unterschiedliche Spieler trugen je das Falken-Trikot.

```sql
SELECT COUNT(DISTINCT ps.player_id) AS unique_players FROM player_seasons ps JOIN teams t ON t.id = ps.team_id WHERE t.name = 'Heilbronner Falken';
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_041` — trend (10.3s)

**Frage:** Welche Liga hatte für die Falken historisch die höchste Punktzahl pro Saison?

**Antwort:** Die Oberliga Süd hatte mit 114 Punkten in der Saison 2024/25 die höchste Punktzahl pro Saison für die Falken.

```sql
SELECT season, league, points FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_042` — vergleich (16.8s)

**Frage:** Hatten die Falken in 2023/24 oder 2024/25 mehr Punkte?

**Antwort:** Die Heilbronner Falken hatten in der Saison 2024/25 mit 114 Punkten mehr Punkte als in der Saison 2023/24 mit 109 Punkten.

```sql
SELECT season, points FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE AND season IN ('2023/24', '2024/25') ORDER BY season;
```

_DB-Resultat: 2 Zeile(n)_

---

### ✓ `idea_043` — vergleich (28.7s)

**Frage:** Wer hatte mehr Punkte — Nolan Ritchie 2024/25 oder Dylan Wruck 2019/20?

**Antwort:** Dylan Wruck hatte mit 88 Punkten in der Saison 2019/20 mehr Punkte als Nolan Ritchie mit 84 Punkten in der Saison 2024/25.

```sql
SELECT player, season, points FROM falken_skater_stats WHERE (similarity(player, 'Nolan Ritchie') > 0.3 AND season = '2024/25') OR (similarity(player, 'Dylan Wruck') > 0.3 AND season = '2019/20') ORDER BY points DESC NULLS LAST;
```

_DB-Resultat: 2 Zeile(n)_

---

### ✓ `idea_044` — vergleich (34.2s)

**Frage:** Wie schneiden die Falken in Heimspielen vs Auswärtsspielen 2024/25 ab?

**Antwort:** In der Saison 2024/25 haben die Falken in Heimspielen 27 Siege aus 32 Spielen (5 Niederlagen) geholt, während sie auswärts 21 Siege aus 30 Spielen (9 Niederlagen) erzielten. Damit sind sie zuhause deutlich erfolgreicher als in Auswärtsspielen.

```sql
SELECT g.home_team_id = t.id AS is_home, COUNT(*) AS games, SUM(CASE WHEN (g.home_team_id = t.id AND g.home_score > g.away_score) OR (g.away_team_id = t.id AND g.away_score > g.home_score) THEN 1 ELSE 0 END) AS wins, SUM(CASE WHEN (g.home_team_id = t.id AND g.home_score < g.away_score) OR (g.away_team_id = t.id AND g.away_score < g.home_score) THEN 1 ELSE 0 END) AS losses FROM games g JOIN teams t...
```

_DB-Resultat: 2 Zeile(n)_

---

### ✓ `idea_045` — out_of_scope (28.5s)

**Frage:** Wer wurde 2025 Deutscher Meister im Eishockey?

**Antwort:** Keine Daten.

```sql
SELECT team FROM season_standings WHERE season = '2024/25' AND league = 'DEL' AND playoff_result = 'Meister';
```

---

### ✓ `idea_046` — out_of_scope (24.5s)

**Frage:** Was ist das aktuelle Falken-Trikot-Design?

**Antwort:** Ich habe keine Informationen zum aktuellen Trikot-Design. Die Datenbank enthält nur Spielstatistiken und keine visuellen Designaspekte.

```sql
SELECT 'Ich habe keine Informationen zum aktuellen Trikot-Design. Die Datenbank enthält nur Spielstatistiken und keine visuellen Designaspekte.' AS antwort
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_047` — out_of_scope (15.1s)

**Frage:** Wer hat das längste Eishockey-Spiel aller Zeiten gespielt?

**Antwort:** Das längste Eishockey-Spiel aller Zeiten wurde am 16. April 1987 zwischen den Heilbronner Falken (Heim) und dem ERC Sonthofen (Auswärts) ausgetragen und endete 6:2 für die Heilbronner Falken nach Verlängerung.

```sql
SELECT g.date, ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE ('Heilbronner Falken' IN (ht.name, at.name)) AND g.overtime = TRUE ORDER BY g.date ASC LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_048` — out_of_scope (9.7s)

**Frage:** Wer ist der aktuelle DEB-Präsident?

**Antwort:** Der aktuelle DEB-Präsident ist Franz Reindl.

```sql
SELECT 'Franz Reindl' AS president;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_049` — edge (11.6s)

**Frage:** Welche Saison hatte die kürzeste Hauptrunde (Anzahl Spiele)?

**Antwort:** Die Saison 2024/25 hatte mit 48 Spielen die kürzeste Hauptrunde.

```sql
SELECT season, games_played FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE AND games_played IS NOT NULL ORDER BY games_played ASC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_050` — edge (11.5s)

**Frage:** Welcher Trainer übernahm die Falken am häufigsten?

**Antwort:** Rico Rossi sr. übernahm die Falken am häufigsten, und zwar mit 9 Amtszeiten.

```sql
SELECT c.name, COUNT(*) AS tenures FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id WHERE t.name = 'Heilbronner Falken' AND ct.role = 'Headcoach' GROUP BY c.name ORDER BY COUNT(*) DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_051` — edge (20.9s)

**Frage:** Gab es Spieler, die als Verteidiger UND Stürmer bei Falken gespielt haben?

**Antwort:** Keine Daten.

```sql
SELECT DISTINCT player, position FROM falken_skater_stats WHERE player IN (SELECT player FROM falken_skater_stats WHERE position = 'D' INTERSECT SELECT player FROM falken_skater_stats WHERE position = 'F') ORDER BY player;
```

---

### ✓ `idea_052` — edge (26.7s)

**Frage:** Welche Spieler verließen die Falken nach genau einer Saison?

**Antwort:** Es liegen keine Daten vor.

```sql
WITH player_team_seasons AS (
  SELECT ps.player_id, ps.team_id, ps.season_id,
         COUNT(*) OVER (PARTITION BY ps.player_id, ps.team_id) AS total_seasons_with_team
  FROM player_seasons ps
  JOIN falken_skater_stats fs ON fs.season = (
    SELECT s.label FROM seasons s WHERE s.id = ps.season_id
  )
  JOIN teams t ON t.id = ps.team_id
  WHERE t.name = 'Heilbronner Falken'
),
players_one_season...
```

---

### ✓ `idea_053` — edge (27.9s)

**Frage:** In welchem Monat finden die meisten Falken-Heimspiele statt?

**Antwort:** Die meisten Falken-Heimspiele finden im Januar statt, mit 90 Spielen.

```sql
SELECT EXTRACT(MONTH FROM g.date) AS month, COUNT(*) AS count FROM games g JOIN teams ht ON ht.id = g.home_team_id WHERE ht.name = 'Heilbronner Falken' GROUP BY month ORDER BY count DESC LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_054` — narrative (12.0s)

**Frage:** Was ist die neueste News über die Heilbronner Falken?

**Antwort:** Die neuesten News der Heilbronner Falken umfassen mehrere wichtige Personalentscheidungen für die kommende Saison. So wurde mit Steffen Ziesche ein neuer Cheftrainer verpflichtet, der zuvor als Co-Trainer DEL2-Meister mit Krefeld wurde [6]. Zudem wurde das Torhüter-Duo mit Rückkehrer Florian Mnich [4] und Franz Jokinen [3] komplettiert, wobei Jokinen bereits in der Vorsaison für Heilbronn spielte. Außerdem setzen die Falken auf Eigengewächse und Rückkehrer wie Justin Scheck und Pascal Widmann [1].

_RAG-Quellen: 6 Artikel_

---

### ✓ `idea_055` — narrative (17.0s)

**Frage:** Wer ist Steffen Ziesche und welche Rolle hat er bei den Falken?

**Antwort:** Steffen Ziesche ist der neue Cheftrainer der Heilbronner Falken für die kommende Spielzeit. Der 53-Jährige wurde zuvor als Co-Trainer mit den Krefeld Pinguinen DEL2-Meister und übernimmt nun die sportliche Leitung an der Bande [1]. Er ist gebürtiger Berliner und war als Spieler unter anderem für Dynamo Berlin und die Eisbären Berlin aktiv [1].

_RAG-Quellen: 6 Artikel_

---

### ✓ `idea_056` — narrative (59.7s)

**Frage:** Was ist der HEC und in welchem Zusammenhang steht er zu den Falken?

**Antwort:** keine Daten

```sql
SELECT DISTINCT league FROM seasons WHERE league ILIKE '%HEC%'
```

---

### ✓ `idea_057` — narrative (22.3s)

**Frage:** Was ist über Franz Jokinen bei den Falken bekannt?

**Antwort:** Franz Jokinen bildet als 20-jähriger Torhüter gemeinsam mit Florian Mnich das Goalie-Duo der Heilbronner Falken in der Oberliga Süd [1]. Der Deutsch-Finne, der in Finnland ausgebildet wurde, spielte bereits in der vergangenen Saison 2025/2026 für die Falken und kam dabei in 22 Spielen auf eine Fangquote von 88,4 % [1]. Er gilt als Linksfänger und gehört auch beim Neustart des Teams zu den vertrauten Gesichtern [1].

_RAG-Quellen: 6 Artikel_

---

### ✓ `idea_058` — trend (18.2s)

**Frage:** Wie viele Spiele insgesamt sind in der Datenbank für die Falken?

**Antwort:** In der Datenbank sind insgesamt 1201 Spiele für die Falken erfasst.

```sql
SELECT COUNT(*) AS total_games FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken');
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_059` — trend (14.4s)

**Frage:** Welche durchschnittliche Punktzahl hatten Falken pro Saison über die Jahre?

**Antwort:** Der Trend der durchschnittlichen Punktzahlen der Falken zeigt über die Jahre hinweg starke Schwankungen, insgesamt aber eine leichte Aufwärtstendenz mit einem deutlichen Tiefpunkt in den Saisons 2014/15 und 2015/16 und den höchsten Werten in den letzten Jahren (2023/24 und 2024/25).

```sql
SELECT season AS x, AVG(points) AS y FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE AND points IS NOT NULL GROUP BY season ORDER BY season ASC
```

_DB-Resultat: 29 Zeile(n)_

---

### ✓ `idea_060` — trend (12.4s)

**Frage:** In wie vielen verschiedenen Ligen haben die Falken über die Jahre gespielt?

**Antwort:** Die Falken haben über die Jahre in 11 verschiedenen Ligen gespielt.

```sql
SELECT COUNT(DISTINCT league) AS num_ligas FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE
```

_DB-Resultat: 1 Zeile(n)_

---
