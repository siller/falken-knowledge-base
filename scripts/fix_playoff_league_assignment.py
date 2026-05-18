"""Fixt falsche Liga-Zuordnung bei Falken-Playoff-Spielen aus eishockey-statistiken.

Der playoff_loader nutzte eine simple Year-basierte Heuristik (yr>=2013 → DEL2),
die für die FALKEN nicht stimmt:
- 2004/05-2006/07: Falken waren Oberliga Süd (nicht 2.BL!)
- 1998/99-2003/04: Falken waren 2.BL (nicht Oberliga!)
- 1995/96-1997/98: Falken waren HPL
- 1994/95: 1.BL Süd
- 1990/91-1993/94: Oberliga Süd

Dieses Skript verschiebt Spiele/Playoff-Series in die korrekte Saison-Liga.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql, supabase

# Verifizierte Falken-Liga-Historie (aus eishockey-statistiken.de)
FALKEN_LEAGUE_BY_YEAR: dict[int, tuple[str, int]] = {
    2025: ("Oberliga Süd", 3),
    2024: ("Oberliga Süd", 3),
    2023: ("Oberliga Süd", 3),
    2022: ("DEL2", 2),
    2021: ("DEL2", 2),
    2020: ("DEL2", 2),
    2019: ("DEL2", 2),
    2018: ("DEL2", 2),
    2017: ("DEL2", 2),
    2016: ("DEL2", 2),
    2015: ("DEL2", 2),
    2014: ("DEL2", 2),
    2013: ("DEL2", 2),
    2012: ("2. Bundesliga", 2),
    2011: ("2. Bundesliga", 2),
    2010: ("2. Bundesliga", 2),
    2009: ("2. Bundesliga", 2),
    2008: ("2. Bundesliga", 2),
    2007: ("2. Bundesliga", 2),
    2006: ("Oberliga Süd", 3),   # Oberliga-MEISTER
    2005: ("Oberliga Süd", 3),
    2004: ("Oberliga Süd", 3),
    2003: ("2. Bundesliga", 2),
    2002: ("2. Bundesliga", 2),
    2001: ("2. Bundesliga", 2),
    2000: ("2. Bundesliga", 2),
    1999: ("2. Bundesliga", 2),
    1998: ("2. Bundesliga", 2),
    1997: ("Hockey Premier League", 2),
    1996: ("Hockey Premier League", 2),
    1995: ("Hockey Premier League", 2),
    1994: ("1. Bundesliga Süd", 1),
    1993: ("Oberliga Süd", 3),
    1992: ("Oberliga Süd", 3),
    1991: ("Oberliga Süd", 3),
    1990: ("Oberliga Süd", 3),
    1988: ("2. Bundesliga Süd", 2),
    1987: ("2. Bundesliga Süd", 2),
    1986: ("Oberliga Nord", 3),
    1985: ("Oberliga Mitte", 3),
    1984: ("Regionalliga Süd-West", 4),
    1983: ("Baden-Württemberg-Liga", 5),
    1982: ("Baden-Württemberg-Liga", 5),
    1981: ("Landesliga BaWü", 5),
    1980: ("Landesliga BaWü", 5),
}


def get_or_create_season(label: str, league: str, tier: int) -> str:
    rows = exec_sql(f"SELECT id FROM falken.seasons WHERE label='{label}' AND league='{league}'")
    if rows:
        return rows[0]["id"]
    ins = supabase().table("falken_seasons").insert({
        "label": label, "league": league, "league_tier": tier,
        "source_ids": {"source": "fix_playoff_league_assignment"},
    }).execute()
    return ins.data[0]["id"]


def move_falken_data_to_correct_league() -> dict:
    """Verschiebt für jede Saison alle Falken-bezogenen Daten in die korrekte Liga-Saison."""
    sb = supabase()
    moves = {"games": 0, "playoff_series": 0, "team_seasons": 0, "deleted_empty_seasons": 0}

    # Für jede Saison mit Falken-Beteiligung
    for yr, (correct_league, correct_tier) in FALKEN_LEAGUE_BY_YEAR.items():
        label = f"{yr}/{(yr + 1) % 100:02d}"

        # Korrekte Ziel-Saison
        correct_id = get_or_create_season(label, correct_league, correct_tier)

        # Alle anderen Saison-Einträge mit gleichem Label (verkehrt zugeordnet)
        wrong = exec_sql(f"""
            SELECT s.id, s.league FROM falken.seasons s
            WHERE s.label = '{label}' AND s.id != '{correct_id}'
        """)

        for w in wrong:
            wid = w["id"]
            # Welche Daten in dieser falschen Saison sind FALKEN-bezogen?
            # 1. games mit Falken-Beteiligung verschieben
            falken_games = exec_sql(f"""
                SELECT g.id FROM falken.games g
                JOIN falken.teams ht ON ht.id = g.home_team_id
                JOIN falken.teams at ON at.id = g.away_team_id
                WHERE g.season_id = '{wid}'
                  AND (ht.name = 'Heilbronner Falken' OR at.name = 'Heilbronner Falken')
            """)
            for g in falken_games:
                sb.table("falken_games").update({"season_id": correct_id}).eq("id", g["id"]).execute()
                moves["games"] += 1

            # 2. playoff_series mit Falken
            falken_ps = exec_sql(f"""
                SELECT ps.id FROM falken.playoff_series ps
                JOIN falken.teams ta ON ta.id = ps.team_a_id
                JOIN falken.teams tb ON tb.id = ps.team_b_id
                WHERE ps.season_id = '{wid}'
                  AND (ta.name = 'Heilbronner Falken' OR tb.name = 'Heilbronner Falken')
            """)
            for p in falken_ps:
                sb.table("falken_playoff_series").update({"season_id": correct_id}).eq("id", p["id"]).execute()
                moves["playoff_series"] += 1

            # 3. team_seasons für Falken in falscher Liga → löschen oder verschieben
            falken_ts = exec_sql(f"""
                SELECT ts.team_id FROM falken.team_seasons ts
                JOIN falken.teams t ON t.id = ts.team_id
                WHERE ts.season_id = '{wid}' AND t.name = 'Heilbronner Falken'
            """)
            for t in falken_ts:
                tid = t["team_id"]
                # Bei conflict mit correct_id-Eintrag: delete den falschen
                exists = exec_sql(f"""
                    SELECT 1 FROM falken.team_seasons
                    WHERE season_id='{correct_id}' AND team_id='{tid}'
                """)
                if exists:
                    sb.table("falken_team_seasons").delete().eq("season_id", wid).eq("team_id", tid).execute()
                else:
                    sb.table("falken_team_seasons").update({"season_id": correct_id}).eq("season_id", wid).eq("team_id", tid).execute()
                moves["team_seasons"] += 1

            # Optional: Saison-Wrapper löschen, wenn sie jetzt LEER ist (kein Team mehr drin)
            remaining = exec_sql(f"""
                SELECT
                    (SELECT COUNT(*) FROM falken.games WHERE season_id = '{wid}') +
                    (SELECT COUNT(*) FROM falken.team_seasons WHERE season_id = '{wid}') +
                    (SELECT COUNT(*) FROM falken.player_seasons WHERE season_id = '{wid}') +
                    (SELECT COUNT(*) FROM falken.playoff_series WHERE season_id = '{wid}') AS total
            """)[0]["total"]
            if remaining == 0:
                sb.table("falken_seasons").delete().eq("id", wid).execute()
                moves["deleted_empty_seasons"] += 1
                print(f"  ✓ {label}: leerer Saison-Wrapper '{w['league']}' gelöscht")

    return moves


if __name__ == "__main__":
    res = move_falken_data_to_correct_league()
    print(f"\n=== Verschoben/bereinigt ===")
    for k, v in res.items():
        print(f"  {k}: {v}")
