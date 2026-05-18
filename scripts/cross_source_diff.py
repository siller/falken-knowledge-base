"""Cross-Source-Diff: vergleicht Daten aus verschiedenen Scrapers re-fetched
live mit den DB-Werten. So sehen wir, ob die Daten noch stimmen + ob unsere
Quellen miteinander konsistent sind.

Vergleich:
1. EliteProspects Topscorer pro Saison vs DB (player_stats)
2. eishockey-statistiken Trainer-Liste vs DB (coach_tenures)
3. del-2.org Spiel-Anzahl pro Saison vs DB
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql
from falken_kb.ingestion.scrapers.elite_prospects import fetch_season_stats
from falken_kb.ingestion.scrapers.eishockey_statistiken import fetch_falken_history


async def diff_topscorer(season: str) -> dict:
    """Vergleich EP-Topscorer mit DB für eine Saison."""
    ep = await fetch_season_stats(season)
    ep_top3 = sorted(ep["players"], key=lambda p: p.get("points") or 0, reverse=True)[:3]
    ep_names = [(p["name"], p.get("points")) for p in ep_top3]

    db_top3 = exec_sql(f"""
        SELECT player, points FROM falken_skater_stats_v
        WHERE season = '{season}'
        ORDER BY points DESC NULLS LAST LIMIT 3
    """)
    db_names = [(r["player"], r["points"]) for r in db_top3]

    return {
        "season": season,
        "ep": ep_names,
        "db": db_names,
        "match": ep_names == db_names,
    }


async def diff_coach_count() -> dict:
    """Vergleich Anzahl Trainer aus eishockey-statistiken vs DB."""
    ehs = await fetch_falken_history()
    # Sammle alle Trainer-Namen aus dem Scrape
    ehs_coaches = set()
    for s in ehs["seasons"]:
        c = s.get("coach")
        if c:
            for name in c.split("/"):
                clean = name.replace("†", "").strip()
                if clean and clean != "---":
                    ehs_coaches.add(clean)

    db_coaches = exec_sql("SELECT name FROM falken.coaches")
    db_names = set(r["name"] for r in db_coaches)

    in_ehs_not_db = ehs_coaches - db_names
    in_db_not_ehs = db_names - ehs_coaches

    return {
        "ehs_count": len(ehs_coaches),
        "db_count": len(db_names),
        "missing_in_db": sorted(in_ehs_not_db),
        "extra_in_db": sorted(in_db_not_ehs),
    }


async def main():
    print("=" * 60)
    print("CROSS-SOURCE DIFF — EP vs eishockey-statistiken vs DB")
    print("=" * 60)

    print("\n## A) Top-3 Scorer pro Saison: EP-Live vs DB")
    for season in ["2022/23", "2021/22", "2019/20", "2017/18"]:
        diff = await diff_topscorer(season)
        marker = "✓" if diff["match"] else "✗"
        print(f"\n  {marker} {season}")
        print(f"    EP-Live: {diff['ep']}")
        print(f"    DB     : {diff['db']}")

    print("\n## B) Trainer-Cross-Check (eishockey-statistiken vs DB)")
    coach = await diff_coach_count()
    print(f"  eishockey-statistiken: {coach['ehs_count']} unique Trainer")
    print(f"  DB                   : {coach['db_count']} Trainer")
    if coach["missing_in_db"]:
        print(f"  Fehlend in DB: {coach['missing_in_db'][:10]}")
    if coach["extra_in_db"]:
        print(f"  Extra in DB  : {coach['extra_in_db'][:10]}")

if __name__ == "__main__":
    asyncio.run(main())
