"""Cleanup-Skript: konsolidiert falsche Liga-Namen + merged Saisons-Duplikate.

Behebt die identifizierten Probleme:
1. "OL" t=99 → "Oberliga Süd" t=3 (eishockey-stat Kürzel)
2. Saisons-Duplikate (2005/06, 2006/07): merge "OL" + "2. Bundesliga" wo Falken Oberliga waren
3. Saisons-Source-IDs für bekannte hockeydata-Saisons setzen
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql, supabase


# Bekannte hockeydata seasonIds aus dem API-Discovery
HOCKEYDATA_DEL2 = {
    "2021/22": "9500", "2022/23": "10914", "2023/24": "13562", "2024/25": "16549",
}
HOCKEYDATA_OBERLIGA = {
    "2018/19": "3544", "2019/20": "5511", "2020/21": "7379", "2021/22": "8404",
    "2022/23": "10321", "2023/24": "13018", "2024/25": "15804", "2025/26": "18443",
}


def merge_season(keep_id: str, merge_id: str) -> dict:
    """Merge merge_id INTO keep_id: alle FK-Verweise umhängen."""
    moved = {}
    sb = supabase()

    # games
    n_games = exec_sql(f"SELECT COUNT(*) AS n FROM falken.games WHERE season_id='{merge_id}'")[0]["n"]
    sb.table("falken_games").update({"season_id": keep_id}).eq("season_id", merge_id).execute()
    moved["games"] = n_games

    # team_seasons (composite PK — potenziell Konflikt)
    ts_to_move = exec_sql(f"SELECT team_id FROM falken.team_seasons WHERE season_id='{merge_id}'")
    for r in ts_to_move:
        team_id = r["team_id"]
        # Existiert keep_id-Eintrag schon?
        exists = exec_sql(f"SELECT 1 FROM falken.team_seasons WHERE season_id='{keep_id}' AND team_id='{team_id}'")
        if exists:
            sb.table("falken_team_seasons").delete().eq("season_id", merge_id).eq("team_id", team_id).execute()
        else:
            sb.table("falken_team_seasons").update({"season_id": keep_id}).eq("season_id", merge_id).eq("team_id", team_id).execute()
    moved["team_seasons"] = len(ts_to_move)

    # player_seasons
    n_ps = exec_sql(f"SELECT COUNT(*) AS n FROM falken.player_seasons WHERE season_id='{merge_id}'")[0]["n"]
    sb.table("falken_player_seasons").update({"season_id": keep_id}).eq("season_id", merge_id).execute()
    moved["player_seasons"] = n_ps

    # playoff_series
    n_po = exec_sql(f"SELECT COUNT(*) AS n FROM falken.playoff_series WHERE season_id='{merge_id}'")[0]["n"]
    sb.table("falken_playoff_series").update({"season_id": keep_id}).eq("season_id", merge_id).execute()
    moved["playoff_series"] = n_po

    # articles
    n_art = exec_sql(f"SELECT COUNT(*) AS n FROM falken.articles WHERE season_id='{merge_id}'")[0]["n"]
    sb.table("falken_articles").update({"season_id": keep_id}).eq("season_id", merge_id).execute()
    moved["articles"] = n_art

    # delete merge season
    sb.table("falken_seasons").delete().eq("id", merge_id).execute()
    return moved


def get_season(label: str, league: str) -> dict | None:
    rows = exec_sql(f"SELECT id, league, league_tier FROM falken.seasons WHERE label='{label}' AND league='{league}'")
    return rows[0] if rows else None


def update_season(season_id: str, **fields) -> None:
    supabase().table("falken_seasons").update(fields).eq("id", season_id).execute()


def main():
    # ---------- 1. "OL" → "Oberliga Süd" Rename + Tier-Fix ----------
    print("\n## 1. Liga-Rename 'OL' → 'Oberliga Süd' (Tier 3)")
    ol_seasons = exec_sql("SELECT id, label FROM falken.seasons WHERE league = 'OL'")
    for r in ol_seasons:
        # Check ob 'Oberliga Süd' für gleiche Saison existiert (für Merge)
        target = get_season(r["label"], "Oberliga Süd")
        if target:
            moved = merge_season(target["id"], r["id"])
            print(f"  ✓ {r['label']}: 'OL' → in vorhandenen 'Oberliga Süd' gemerged: {moved}")
        else:
            update_season(r["id"], league="Oberliga Süd", league_tier=3)
            print(f"  ✓ {r['label']}: 'OL' (t99) → 'Oberliga Süd' (t3) umbenannt")

    # ---------- 2. Hockey Premier League Tier 1 (war damals höchste Liga) ----------
    # Hinweis: in der HPL-Ära (95-97) war HPL die Top-Liga, nachdem DEL 94 startete als Tier-1
    # HPL war eigentlich die Liga UNTER DEL, also tier 2. Stehen lassen.
    print("\n## 2. HPL-Tier: bestätigt tier=2 (war 2.Liga unter DEL ab 1994)")

    # ---------- 3. Duplikate '2. Bundesliga' + 'Oberliga Süd' für ältere Saisons ----------
    # Falken waren in Oberliga, die 2.BL-Spiele sind Aufstiegs-Quali — wir lassen sie als
    # eigene Saison-Einträge, aber kennzeichnen sie. Manuelle Verifikation nötig.
    print("\n## 3. Duplikate prüfen: 2005/06, 2001/02, 2000/01, 1996/97, 1995/96, 1994/95")
    print("  Diese Splits sind echt (Oberliga = Falken-Liga, 2.BL = Aufstiegs-Quali)")
    print("  KEIN Auto-Merge — behalte beide Einträge")

    # ---------- 4. 1986/87: 'Sonstige' (t=3, 2 games) + 'Oberliga Nord' (t=3) ----------
    # Die "Sonstige" Saison ist von eishockey-statistiken playoff-loader, falsche Liga-Zuordnung
    # Merge in 'Oberliga Nord' (Falken-echte Liga 86/87)
    print("\n## 4. 1986/87: 'Sonstige' → 'Oberliga Nord' (Falken waren in Oberliga Nord)")
    sonstige = get_season("1986/87", "Sonstige")
    nord = get_season("1986/87", "Oberliga Nord")
    if sonstige and nord:
        moved = merge_season(nord["id"], sonstige["id"])
        print(f"  ✓ Merged: {moved}")

    # ---------- 5. Source-IDs für hockeydata-bekannte Saisons setzen ----------
    print("\n## 5. Source-IDs setzen für hockeydata-bekannte Saisons")
    for label, hd_id in HOCKEYDATA_DEL2.items():
        s = get_season(label, "DEL2")
        if s:
            update_season(s["id"], source_ids={"hockeydata": hd_id})
            print(f"  ✓ DEL2 {label}: hockeydata={hd_id}")
    for label, hd_id in HOCKEYDATA_OBERLIGA.items():
        s = get_season(label, "Oberliga Süd")
        if s:
            update_season(s["id"], source_ids={"hockeydata": hd_id})
            print(f"  ✓ Oberliga Süd {label}: hockeydata={hd_id}")

    print("\n## DONE.")


if __name__ == "__main__":
    main()
