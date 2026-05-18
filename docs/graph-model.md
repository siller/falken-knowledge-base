# Graph-Modell — Postgres ↔ Neo4j Mapping

Dieses Dokument beschreibt die exakte Übersetzung von Phase-1-Postgres-Tabellen
in Phase-2-Neo4j-Nodes und -Relationships.

Ziel: Phase 2 ist umsetzbar, indem ein Worker `sync_log` polled und gemäß dem
Mapping unten Cypher-Statements gegen Neo4j absetzt. Kein Phase-1-Code wird angefasst.

## Neo4j-Labels (Knoten)

| Postgres-Tabelle | Neo4j-Label | Eigenschaften |
|---|---|---|
| `seasons` | `:Season` | id, label, league, league_tier, start_date, end_date |
| `teams` | `:Team` | id, name, short_name, city, arena, founded_year |
| `players` | `:Player` | id, name, position, nation, birthdate, height_cm, weight_kg, shoots |
| `coaches` | `:Coach` | id, name, nation, birthdate |
| `games` | `:Game` | id, date, game_type, home_score, away_score, overtime, shootout, venue, attendance |
| `articles` | `:Article` | id, source, url, published_at, title, summary |

Die `id` ist die Postgres-UUID (identisch in beiden Systemen).

## Neo4j-Relationships (Kanten)

| Postgres-Tabelle | Cypher | Eigenschaften |
|---|---|---|
| `team_seasons` | `(Team)-[:PLAYED_IN]->(Season)` | final_rank, points, wins, losses, gf, ga, playoff_result |
| `player_seasons` | `(Player)-[:SKATED_FOR {jersey, role}]->(Team)` plus `(Player)-[:PLAYED_SEASON]->(Season)` | beide aus player_seasons |
| `coach_tenures` | `(Coach)-[:COACHED {role, start_date, end_date}]->(Team)` | |
| `games.home_team_id` | `(Game)-[:HOME_TEAM]->(Team)` | |
| `games.away_team_id` | `(Game)-[:AWAY_TEAM]->(Team)` | |
| `games.season_id` | `(Game)-[:IN_SEASON]->(Season)` | |
| `game_events` | `(Game)-[:HAD_EVENT]->(Event)` plus `(Player)-[:DID_EVENT]->(Event)` | type, period, time, description |
| `playoff_series` | `(Series:PlayoffSeries)` plus `(Series)-[:IN_SEASON]->(Season)` plus `(Team)-[:IN_SERIES]->(Series)` | round, wins_a, wins_b |
| `articles.season_id` | `(Article)-[:ABOUT_SEASON]->(Season)` | |
| `articles.game_id` | `(Article)-[:ABOUT_GAME]->(Game)` | |

## Sync-Log-Schema

`sync_log` zeichnet jede Mutation auf:
- `table_name` — Postgres-Tabelle
- `row_id` — UUID der Row (NULL bei Composite-PKs)
- `composite_key` — JSONB für Composite-PKs (z.B. `{team_id, season_id}`)
- `op` — `I`/`U`/`D`
- `payload` — Vollständige neue/alte Row als JSONB
- `occurred_at` — Timestamp
- `replicated_to` — JSONB, von Replikations-Workern beschrieben (z.B. `{"neo4j": "2026-05-17T12:00:00Z"}`)

## Phase-2-Worker-Pseudocode

```python
while True:
    rows = pg.fetch("""
        SELECT * FROM falken.sync_log
        WHERE NOT (replicated_to ? 'neo4j')
        ORDER BY id LIMIT 100
    """)
    for r in rows:
        cypher = TABLE_TO_CYPHER[r.table_name](r.op, r.payload)
        neo4j.execute(cypher)
        pg.execute(
            "UPDATE falken.sync_log SET replicated_to = replicated_to || %s WHERE id = %s",
            ({'neo4j': now()}, r.id)
        )
    sleep(2)
```

## Beispiel-Cypher-Queries (für Phase 2)

```cypher
-- Welche Spieler haben sowohl für Falken als auch für Bietigheim gespielt?
MATCH (p:Player)-[:SKATED_FOR]->(t:Team {name: 'Heilbronner Falken'})
MATCH (p)-[:SKATED_FOR]->(t2:Team {name: 'Bietigheim Steelers'})
RETURN DISTINCT p.name

-- Welche Trainer waren bei wie vielen DEL2-Teams?
MATCH (c:Coach)-[:COACHED]->(t:Team)-[:PLAYED_IN]->(s:Season {league: 'DEL2'})
RETURN c.name, count(DISTINCT t) AS teams
ORDER BY teams DESC

-- Linemates: wer hat mit wem die meisten Tore zusammen geschossen?
MATCH (g:Game)-[:HAD_EVENT]->(e:Event {type: 'goal'})
WHERE size(e.assists) > 0
MATCH (p1:Player)-[:DID_EVENT]->(e)
UNWIND e.assists AS aid
MATCH (p2:Player {id: aid})
RETURN p1.name, p2.name, count(*) AS goals_together
ORDER BY goals_together DESC LIMIT 20
```
