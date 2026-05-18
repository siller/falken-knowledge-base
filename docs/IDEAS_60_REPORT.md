# Brainstorm-Test: 60 eigene Fragen

**Quelle:** `tests/ideas_60_results.json`

## Zusammenfassung

| Metrik | Wert |
|---|---|
| Tests gesamt | **40** |
| Brauchbare Antworten | **36** (90 %) |
| Leere Antworten | 2 |
| SQL-Fehler | 2 |

## Per Kategorie

| Kategorie | OK | Empty | Err |
|---|---:|---:|---:|
| goalie | 4 | 0 | 0 |
| liga | 1 | 0 | 2 |
| playoff | 5 | 0 | 0 |
| saison_platz | 1 | 0 | 0 |
| saison_punkte | 1 | 0 | 0 |
| spieler | 8 | 0 | 0 |
| spielergebnis | 4 | 2 | 0 |
| topscorer | 1 | 0 | 0 |
| trainer | 5 | 0 | 0 |
| trend | 4 | 0 | 0 |
| vergleich | 2 | 0 | 0 |

## Einzelergebnisse

### 💥 `idea_001` — liga (11.0s)

**Frage:** In welcher Liga spielen die Heilbronner Falken aktuell?

**Antwort:** ⚠️  Konnte die Frage nicht beantworten (SQL-Fehler: {'code': '42P10', 'details': None, 'hint': None, 'message': 'for SELECT DISTINCT, ORDER BY expressions must appear in select list'}).

```sql
SELECT DISTINCT league FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE ORDER BY season DESC LIMIT 1
```

---

### ✓ `idea_002` — saison_platz (8.2s)

**Frage:** Wo standen die Falken am Ende der Hauptrunde 2025/26?

**Antwort:** Die Heilbronner Falken belegten am Ende der Hauptrunde 2025/26 den 5. Platz mit 93 Punkten.

```sql
SELECT final_rank, points FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2025/26';
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_003` — saison_punkte (9.4s)

**Frage:** Wie viele Punkte hatten die Falken in der gesamten Saisongeschichte zusammen?

**Antwort:** Die Falken hatten in der gesamten Saisongeschichte insgesamt 2199 Punkte.

```sql
SELECT SUM(points) AS total_points FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_004` — liga (21.1s)

**Frage:** Wie lange spielten die Heilbronner Falken in der DEL2 insgesamt?

**Antwort:** Die Heilbronner Falken spielten insgesamt 10 Saisons in der DEL2, von September 2013 bis Mai 2023.

```sql
SELECT COUNT(DISTINCT s.label) AS seasons_in_del2, MIN(s.start_date) AS first_season_start, MAX(s.end_date) AS last_season_end FROM season_standings ss JOIN seasons s ON s.label = ss.season WHERE ss.team = 'Heilbronner Falken' AND ss.league = 'DEL2' AND ss.is_focus_team_season = TRUE;
```

_DB-Resultat: 1 Zeile(n)_

---

### 💥 `idea_005` — liga (14.8s)

**Frage:** Wann sind die Falken aus der DEL2 abgestiegen?

**Antwort:** ⚠️  Konnte die Frage nicht beantworten (SQL-Fehler: {'code': '42703', 'details': None, 'hint': 'Perhaps you meant to reference the column "s.league".', 'message': 'column ts.league does not exist'}).

```sql
SELECT s.label, ts.final_rank FROM team_seasons ts JOIN seasons s ON s.id = ts.season_id JOIN teams t ON t.id = ts.team_id WHERE t.name = 'Heilbronner Falken' AND ts.league = 'DEL2' ORDER BY s.start_date DESC LIMIT 1;
```

---

### ✓ `idea_006` — trainer (16.4s)

**Frage:** Wer ist aktuell Trainer der Falken?

**Antwort:** Der aktuelle Trainer der Falken ist Francesco Petrozza.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date WHERE t.name = 'Heilbronner Falken' AND s.label = '2024/25' AND ct.role = 'Headcoach' ORDER BY ct.start_date DESC LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_007` — topscorer (23.5s)

**Frage:** Wer ist aktueller Topscorer der Falken?

**Antwort:** Calder ANDERSON ist aktueller Topscorer der Falken mit 68 Punkten (30 Tore, 38 Assists).

```sql
WITH current_season AS (SELECT season FROM season_standings WHERE team = 'Heilbronner Falken' ORDER BY season DESC LIMIT 1) SELECT player, points, goals, assists FROM falken_skater_stats WHERE season = (SELECT season FROM current_season) AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_008` — spielergebnis (21.4s)

**Frage:** Was war das letzte Heimspiel der Falken?

**Antwort:** Das letzte Heimspiel der Falken war am 22. Februar 2026 eine 2:7-Niederlage gegen die Erding Gladiators.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.date, g.overtime, g.shootout FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE ht.name = 'Heilbronner Falken' ORDER BY g.date DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_009` — vergleich (44.4s)

**Frage:** Wie viele Siege haben die Falken in der aktuellen Saison?

**Antwort:** Die Falken haben in der aktuellen Saison 27 Siege erzielt.

```sql
SELECT wins FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE ORDER BY season DESC LIMIT 1
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_010` — vergleich (10.2s)

**Frage:** Wie viele Tore haben die Falken in der laufenden Saison erzielt?

**Antwort:** Die Falken haben in der laufenden Saison 208 Tore erzielt.

```sql
SELECT goals_for FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE ORDER BY season DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_011` — spieler (9.4s)

**Frage:** Wie viele Saisons spielte Nolan Ritchie für die Falken?

**Antwort:** Nolan Ritchie spielte 2 Saisons für die Falken.

```sql
SELECT COUNT(DISTINCT season) AS seasons_played FROM falken_skater_stats WHERE similarity(player, 'Nolan Ritchie') > 0.3;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_012` — spieler (16.0s)

**Frage:** Was war die beste Saison von Dylan Wruck punktemäßig?

**Antwort:** Die beste Saison von Dylan Wruck punktemäßig war die Saison 2019/20 mit 88 Punkten (24 Tore und 64 Vorlagen).

```sql
SELECT season, points, goals, assists FROM falken_skater_stats WHERE similarity(player, 'Dylan Wruck') > 0.3 AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_013` — spieler (25.2s)

**Frage:** Hat Dylan Wruck mehr als 200 Karriere-Punkte für die Falken?

**Antwort:** Nein, Dylan Wruck hat 166 Karriere-Punkte für die Falken, also weniger als 200.

```sql
SELECT SUM(points) AS career_points FROM falken_skater_stats WHERE similarity(player, 'Dylan Wruck') > 0.3 AND points IS NOT NULL;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_014` — spieler (16.1s)

**Frage:** Welche Nationalität hatte Robert Hock?

**Antwort:** Der Geburtsort von Robert Hock ist nicht in den Daten vorhanden.

```sql
SELECT nation FROM players WHERE name ILIKE '%Robert Hock%' LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_015` — spieler (16.8s)

**Frage:** Wer trug das Trikot mit Nummer 10 in der Saison 2024/25?

**Antwort:** Es liegen keine Daten zur Trikotnummer 10 in der Saison 2024/25 vor.

```sql
SELECT player FROM falken_skater_stats WHERE season = '2024/25' AND jersey_number = 10;
```

---

### ✓ `idea_016` — spieler (12.8s)

**Frage:** Wie viele Tore hat Nolan Ritchie in der Saison 2024/25 erzielt?

**Antwort:** Nolan Ritchie hat in der Saison 2024/25 38 Tore erzielt.

```sql
SELECT season, player, goals FROM falken_skater_stats WHERE similarity(player, 'Nolan Ritchie') > 0.3 AND season = '2024/25' AND goals IS NOT NULL ORDER BY similarity(player, 'Nolan Ritchie') DESC LIMIT 1
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_017` — spieler (24.8s)

**Frage:** Welche Spieler hatten mehr als 80 Punkte in einer Saison bei den Falken?

**Antwort:** Pontus Wernerson Libäck (90 Punkte in 2023/24), Linus Wernerson Libäck (89 Punkte in 2023/24), Dylan Wruck (88 Punkte in 2019/20), Nolan Ritchie (84 Punkte in 2024/25) und Calder Anderson (81 Punkte in 2024/25) erzielten mehr als 80 Punkte in einer Saison bei den Falken.

```sql
SELECT player, season, points, goals, assists FROM falken_skater_stats WHERE points > 80 ORDER BY points DESC;
```

_DB-Resultat: 5 Zeile(n)_

---

### ✓ `idea_018` — spieler (28.5s)

**Frage:** Hat Calder Anderson in 2025/26 mehr Tore als Vorlagen?

**Antwort:** Nein, Calder Anderson hat in der Saison 2025/26 nicht mehr Tore als Vorlagen erzielt.

```sql
SELECT (goals > assists) AS more_goals_than_assists FROM falken_skater_stats WHERE similarity(player, 'Calder Anderson') > 0.3 AND season = '2025/26' AND goals IS NOT NULL AND assists IS NOT NULL ORDER BY similarity(player, 'Calder Anderson') DESC LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_019` — goalie (24.1s)

**Frage:** Wer war der beste Torhüter der Falken in der Saison 2024/25 nach Gegentor-Schnitt?

**Antwort:** Der beste Torhüter der Falken in der Saison 2024/25 nach Gegentor-Schnitt war Patrick BERGER mit einem GAA von 2,73.

```sql
SELECT goalie, gaa, save_pct, shutouts FROM falken_goalie_stats WHERE season = '2024/25' AND gaa IS NOT NULL ORDER BY gaa ASC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_020` — goalie (16.2s)

**Frage:** Welche Torhüter spielten 2025/26 für die Falken?

**Antwort:** In der Saison 2025/26 spielten Konrad MARKUS (Trikotnummer 1) und Julian SCHMITT (Trikotnummer 22) für die Falken.

```sql
SELECT goalie, jersey_number, games_played, wins, losses, gaa, save_pct AS save_pct, gaa, shutouts FROM falken_goalie_stats WHERE season = '2025/26' ORDER BY games_played DESC NULLS LAST
```

_DB-Resultat: 2 Zeile(n)_

---

### ✓ `idea_021` — goalie (22.2s)

**Frage:** Wie viele Siege hatte Nico Zimmermann in der Saison 2024/25?

**Antwort:** Nico Zimmermann hatte in der Saison 2024/25 18 Siege.

```sql
SELECT wins FROM goalie_stats gs JOIN player_seasons ps ON gs.player_season_id = ps.id JOIN players p ON ps.player_id = p.id JOIN seasons s ON ps.season_id = s.id WHERE similarity(p.name, 'Nico Zimmermann') > 0.3 AND s.label = '2024/25' AND wins IS NOT NULL
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_022` — goalie (12.8s)

**Frage:** Hatte Michael Paterson-Jones in 24/25 eine bessere Save-Quote als Nico Zimmermann?

**Antwort:** Nein, Michael Paterson-Jones hatte in der Saison 24/25 mit einer Save-Quote von 0,902 eine schlechtere Quote als Nico Zimmermann mit 0,905.

```sql
SELECT goalie, save_pct FROM falken_goalie_stats WHERE season = '2024/25' AND (similarity(goalie, 'Michael Paterson-Jones') > 0.3 OR similarity(goalie, 'Nico Zimmermann') > 0.3) ORDER BY save_pct DESC;
```

_DB-Resultat: 2 Zeile(n)_

---

### ✓ `idea_023` — trainer (18.2s)

**Frage:** Wie lange war Rico Rossi Trainer der Falken?

**Antwort:** Rico Rossi sr. war 8 Jahre Trainer der Falken, von  (von 2004-09-01 bis 2013-05-31).

```sql
SELECT c.name, MIN(ct.start_date) AS  start_date, MAX(ct.end_date) AS end_date, EXTRACT(YEAR FROM AGE(MAX(ct.end_date), MIN(ct.start_date))) AS years_active FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id WHERE t.name = 'Heilbronner Falken' AND similarity(c.name, 'Rico Rossi') > 0.3 AND ct.role = 'Headcoach' GROUP BY c.name;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_024` — trainer (19.6s)

**Frage:** Welcher Trainer hatte die längste durchgehende Amtszeit bei den Falken?

**Antwort:** Georges Hüttig hatte die längste durchgehende Amtszeit bei den Falken mit einer Dauer von 273 Tagen (vom 1. September 1983 bis 31. Mai 1984).

```sql
SELECT c.name, ct.start_date, ct.end_date, (ct.end_date - ct.start_date) AS tenure_days FROM coach_tenures ct JOIN coaches c ON c.id = ct.coach_id JOIN teams t ON t.id = ct.team_id WHERE t.name = 'Heilbronner Falken' AND ct.role = 'Headcoach' AND ct.end_date IS NOT NULL AND ct.start_date IS NOT NULL ORDER BY (ct.end_date - ct.start_date) DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_025` — trainer (25.3s)

**Frage:** Wer war der erste Trainer der Falken überhaupt?

**Antwort:** Der erste Trainer der Falken war Josef Matousek, der am 1. September 1980 als Headcoach begann.

```sql
SELECT c.name, ct.role, MIN(ct.start_date) AS first_start
FROM coach_tenures ct
JOIN coaches c ON c.id = ct.coach_id
JOIN teams t ON t.id = ct.team_id
WHERE t.name = 'Heilbronner Falken' AND ct.role = 'Headcoach'
GROUP BY c.name, ct.role
ORDER BY first_start ASC
LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_026` — trainer (14.1s)

**Frage:** Wer war Trainer der Falken in der Klassenerhalt-Saison 2015/16?

**Antwort:** In der Klassenerhalt-Saison 2015/16 waren Manfred Wolf und Fabian Dahlem als Headcoach für die Falken tätig.

```sql
SELECT c.name, ct.role, ct.start_date, ct.end_date
FROM coach_tenures ct
JOIN coaches c ON c.id = ct.coach_id
JOIN teams t ON t.id = ct.team_id
JOIN seasons s ON ct.start_date <= s.end_date AND ct.end_date >= s.start_date
WHERE t.name = 'Heilbronner Falken' AND s.label = '2015/16' AND ct.role = 'Headcoach';
```

_DB-Resultat: 2 Zeile(n)_

---

### ✓ `idea_027` — playoff (23.3s)

**Frage:** Wie weit kamen die Falken in den Oberliga-Süd Playoffs 2024/25?

**Antwort:** Die Daten enthalten kein Playoff-Ergebnis für die Heilbronner Falken in der Oberliga-Süd 2024/25 – es liegen keine Daten vor.

```sql
SELECT playoff_result FROM season_standings WHERE team = 'Heilbronner Falken' AND season = '2024/25' AND league = 'Oberliga Süd'
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_028` — playoff (34.3s)

**Frage:** Welche Teams haben die Falken im Viertelfinale 2023/24 besiegt?

**Antwort:** Die Heilbronner Falken haben im Viertelfinale 2023/24 die ECDC Memmingen Indians mit 4:1 Siegen besiegt.

```sql
SELECT ta.name AS team_a, tb.name AS team_b, ps.round, ps.wins_a, ps.wins_b, wt.name AS winner FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id LEFT JOIN teams wt ON wt.id = ps.winner_team_id JOIN seasons s ON s.id = ps.season_id WHERE s.label = '2023/24' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND ps.round = 'Viertelfinale'
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_029` — playoff (14.4s)

**Frage:** Wie viele Playoff-Serien haben die Falken in der DEL2-Zeit gewonnen?

**Antwort:** Die Falken haben in der DEL2-Zeit 4 Playoff-Serien gewonnen.

```sql
WITH falken_id AS (SELECT id FROM teams WHERE name = 'Heilbronner Falken') SELECT COUNT(*) AS playoff_series_gewonnen FROM playoff_series ps JOIN seasons s ON s.id = ps.season_id, falken_id f WHERE s.league = 'DEL2' AND (ps.team_a_id = f.id OR ps.team_b_id = f.id) AND ps.winner_team_id = f.id;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_030` — playoff (21.9s)

**Frage:** Welches Team hat die Falken am häufigsten in den Playoffs eliminiert?

**Antwort:** Das Team, das die Falken am häufigsten in den Playoffs eliminiert hat, ist der ESV Kaufbeuren mit 2 Eliminierungen.

```sql
SELECT opponent, eliminations FROM (SELECT CASE WHEN ta.name = 'Heilbronner Falken' THEN tb.name ELSE ta.name END AS opponent, COUNT(DISTINCT ps.season_id) AS eliminations FROM playoff_series ps JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id JOIN seasons s ON s.id = ps.season_id WHERE ('Heilbronner Falken' IN (ta.name, tb.name)) AND ps.winner_team_id IS NOT NULL AND ps...
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_031` — playoff (13.2s)

**Frage:** Wie viele Playdown-Serien spielten die Falken in der DEL2?

**Antwort:** Die Falken spielten 7 Playdown-Serien in der DEL2.

```sql
SELECT COUNT(*) AS playdown_series_count FROM playoff_series ps JOIN seasons s ON s.id = ps.season_id JOIN teams ta ON ta.id = ps.team_a_id JOIN teams tb ON tb.id = ps.team_b_id WHERE s.league = 'DEL2' AND ('Heilbronner Falken' IN (ta.name, tb.name)) AND (ps.round = 'Play-Down R1' OR ps.round = 'Play-Down R2');
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_032` — spielergebnis (44.1s)

**Frage:** Was war das höchste Tor-Ergebnis der Falken in einem einzelnen Spiel?

**Antwort:** Das höchste Tor-Ergebnis der Heilbronner Falken in einem einzelnen Spiel war 12 Tore beim 12:6-Sieg gegen den SC Riessersee.

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id WHERE ('Heilbronner Falken' IN (ht.name, at.name)) ORDER BY GREATEST(g.home_score, g.away_score) DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ⚠️ `idea_033` — spielergebnis (25.2s)

**Frage:** Was war die höchste Niederlage der Falken in einem Spiel?

**Antwort:** _(leer)_

```sql
SELECT g.home_score, g.away_score, g.overtime, g.shootout, ht.name AS home_team, at.name AS away_team, g.date::date AS spieltag, (abs(g.home_score - g.away_score)) AS tore_diff FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id JOIN seasons s ON s.id = g.season_id WHERE (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken') AND ((ht.name = 'Hei...
```

_DB-Resultat: 1 Zeile(n)_

---

### ⚠️ `idea_034` — spielergebnis (20.6s)

**Frage:** Wie oft haben die Falken in der Saison 2025/26 gegen Memmingen gespielt und mit welchen Ergebnissen?

**Antwort:** _(leer)_

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, g.overtime, g.shootout, g.date FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id JOIN seasons s ON s.id = g.season_id WHERE s.label = '2025/26' AND ('Heilbronner Falken' IN (ht.name, at.name)) AND ('ECDC Memmingen Indians' IN (ht.name, at.name)) ORDER BY g.date;
```

_DB-Resultat: 4 Zeile(n)_

---

### ✓ `idea_035` — spielergebnis (15.5s)

**Frage:** Wie viele Spiele endeten in der Saison 2024/25 in Overtime?

**Antwort:** In der Saison 2024/25 endeten 55 Spiele in Overtime.

```sql
SELECT COUNT(*) AS overtime_games FROM games g JOIN seasons s ON s.id = g.season_id WHERE s.label = '2024/25' AND g.overtime = TRUE;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_036` — spielergebnis (24.8s)

**Frage:** Welches Spiel hatte die meisten Gesamttore in der Saison 2023/24?

**Antwort:** Das Spiel mit den meisten Gesamttoren in der Saison 2023/24 war die Partie zwischen dem ECDC Memmingen Indians und den Heilbronner Falken mit 13 Toren (7:6).

```sql
SELECT ht.name AS home_team, at.name AS away_team, g.home_score, g.away_score, (g.home_score + g.away_score) AS total_goals FROM games g JOIN teams ht ON ht.id = g.home_team_id JOIN teams at ON at.id = g.away_team_id JOIN seasons s ON s.id = g.season_id WHERE s.label = '2023/24' AND (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken') AND g.home_score IS NOT NULL AND g.away_score IS ...
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_037` — trend (11.6s)

**Frage:** In welcher Saison hatten die Falken die meisten Tore?

**Antwort:** In der Saison 1986/87 hatten die Falken mit 296 Toren die meisten Tore.

```sql
SELECT season, goals_for FROM season_standings WHERE team = 'Heilbronner Falken' AND is_focus_team_season = TRUE AND goals_for IS NOT NULL ORDER BY goals_for DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_038` — trend (6.9s)

**Frage:** Welcher Spieler hat in der Falken-Geschichte die meisten Karriere-Tore?

**Antwort:** Der Spieler mit den meisten Karriere-Toren in der Falken-Geschichte ist Justin Kirsch, der insgesamt 139 Tore erzielt hat.

```sql
SELECT player, SUM(goals) AS career_goals FROM falken_skater_stats WHERE goals IS NOT NULL GROUP BY player ORDER BY career_goals DESC NULLS LAST LIMIT 1;
```

_DB-Resultat: 1 Zeile(n)_

---

### ✓ `idea_039` — trend (49.0s)

**Frage:** Wie hat sich die Tordifferenz der Falken in den letzten 5 Saisons entwickelt?

**Antwort:** Die Tordifferenz der Falken schwankte in den letzten fünf Saisons stark: Nach einem negativen Wert von -19 in der Saison 2022/23 stieg sie rasant auf 109 und 142 in den folgenden Jahren, bevor sie in 2025/26 wieder auf 46 fiel.

```sql
SELECT season AS x, goal_diff AS y FROM season_standings WHERE team = 'Heilbronner Falken' AND season >= '2018/19' AND goal_diff IS NOT NULL ORDER BY season ASC
```

_DB-Resultat: 8 Zeile(n)_

---

### ✓ `idea_040` — trend (8.9s)

**Frage:** Wie viele unterschiedliche Spieler trugen je das Falken-Trikot?

**Antwort:** 230 unterschiedliche Spieler trugen je das Falken-Trikot.

```sql
SELECT COUNT(DISTINCT ps.player_id) FROM player_seasons ps JOIN teams t ON t.id = ps.team_id WHERE t.name = 'Heilbronner Falken';
```

_DB-Resultat: 1 Zeile(n)_

---
