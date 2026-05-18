"""Cross-Source-Dedup-Utilities.

Aktuell brauchen wir das nur defensiv: EP ist die einzige Spieler-Stats-Quelle,
und upsert_player matcht über exakten Namen. Für künftige Quellen-Ergänzung
(z.B. wenn rodi-db irgendwann wieder live ist oder neue Datenquellen dazukommen)
bieten wir hier Name-Normalisierung + Fuzzy-Match.

Plus: einmal über die DB iterieren und gleichartige Spieler mergen (manuelle
Bestätigung empfohlen).
"""
from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

from rapidfuzz import fuzz

from ..db import exec_sql, supabase

logger = logging.getLogger(__name__)


def normalize_name(name: str) -> str:
    """Kanonische Form für Player-Namen.

    'Alex Tonge'   → 'alex tonge'
    'Linus Wernerson Libäck' → 'linus wernerson libaeck' (Umlaute, lowercase, dedup spaces)
    """
    if not name:
        return ""
    # Unicode-Normalisierung (NFKD, ASCII-Approx)
    n = unicodedata.normalize("NFKD", name)
    # Umlaute manuell — NFKD löst nur kombinierende Akzente
    n = n.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    n = n.replace("Ä", "ae").replace("Ö", "oe").replace("Ü", "ue")
    # Lowercase
    n = n.lower()
    # Trim + dedup spaces + remove punctuation
    n = re.sub(r"[^\w\s-]", " ", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def is_likely_same_player(name_a: str, name_b: str, threshold: int = 88) -> bool:
    """Fuzzy-Vergleich zweier Spielernamen via rapidfuzz."""
    a = normalize_name(name_a)
    b = normalize_name(name_b)
    if a == b:
        return True
    # token_sort_ratio ist robust gegenüber unterschiedlicher Wortreihenfolge
    return fuzz.token_sort_ratio(a, b) >= threshold


def find_duplicate_players_in_db(limit: int = 50) -> list[dict[str, Any]]:
    """Sucht potenzielle Duplikate in der DB. Returns Vorschlagsliste zum Manual-Review.

    Strategie: für jeden Spieler, finde alle anderen mit gleichem normalisierten
    Namen oder Trigram-Ähnlichkeit > 0.7. Output ist eine Liste von Paaren mit
    Fuzzy-Score, damit der User entscheiden kann, welche tatsächlich Duplikate sind.
    """
    # Hole alle Spieler-Namen
    rows = exec_sql("SELECT id, name FROM falken.players ORDER BY name")
    candidates: list[dict[str, Any]] = []

    # Bucketing über normalized name
    norm_map: dict[str, list[tuple[str, str]]] = {}
    for r in rows:
        norm = normalize_name(r["name"])
        norm_map.setdefault(norm, []).append((r["id"], r["name"]))

    # Pairs in same bucket
    for norm, players in norm_map.items():
        if len(players) > 1:
            for i in range(len(players)):
                for j in range(i + 1, len(players)):
                    candidates.append({
                        "type": "exact_after_normalize",
                        "id_a": players[i][0], "name_a": players[i][1],
                        "id_b": players[j][0], "name_b": players[j][1],
                        "score": 100,
                    })

    # Fuzzy zwischen unterschiedlichen Buckets (paarweise, O(N²) — bei 154 Spielern OK)
    all_names = list(norm_map.items())
    for i in range(len(all_names)):
        for j in range(i + 1, len(all_names)):
            n1, players1 = all_names[i]
            n2, players2 = all_names[j]
            score = fuzz.token_sort_ratio(n1, n2)
            if score >= 88:
                for p1 in players1:
                    for p2 in players2:
                        candidates.append({
                            "type": "fuzzy",
                            "id_a": p1[0], "name_a": p1[1],
                            "id_b": p2[0], "name_b": p2[1],
                            "score": score,
                        })

    candidates.sort(key=lambda c: -c["score"])
    return candidates[:limit]


def merge_players(keep_id: str, merge_id: str) -> dict[str, int]:
    """Merged merge_id INTO keep_id: alle player_seasons + player_stats werden umgehängt.

    ACHTUNG: irreversibel. Vor Aufruf Vorschlagsliste reviewen.
    """
    # Update via direkter RPC oder Service-Role nicht möglich (exec_sql ist SELECT-only).
    # Wir nutzen die supabase-py table().update():
    moved_ps = 0
    # Hole player_seasons-IDs für merge_id
    ps_to_move = exec_sql(f"SELECT id FROM falken.player_seasons WHERE player_id = '{merge_id}'")
    for ps in ps_to_move:
        try:
            supabase().table("falken_player_seasons").update({"player_id": keep_id}).eq("id", ps["id"]).execute()
            moved_ps += 1
        except Exception as e:
            logger.warning("Move player_season %s failed: %s", ps["id"], e)

    # Lösche merge_id (CASCADE löscht player_stats die noch über ps verlinkt sind)
    try:
        supabase().table("falken_players").delete().eq("id", merge_id).execute()
    except Exception as e:
        logger.error("Delete player %s failed: %s", merge_id, e)
        return {"moved_player_seasons": moved_ps, "deleted_player": 0}
    return {"moved_player_seasons": moved_ps, "deleted_player": 1}


def find_duplicate_teams_in_db(min_score: int = 80) -> list[dict[str, Any]]:
    """Wie find_duplicate_players, aber für Teams (mit niedrigerem Threshold
    weil Team-Namen mehr Variationen haben: 'EHC Bayreuth Tigers' vs 'Bayreuth Tigers').
    """
    rows = exec_sql("SELECT id, name FROM falken.teams ORDER BY name")
    candidates: list[dict[str, Any]] = []
    n = len(rows)
    for i in range(n):
        for j in range(i + 1, n):
            a = normalize_name(rows[i]["name"])
            b = normalize_name(rows[j]["name"])
            score = fuzz.token_set_ratio(a, b)  # token_set ist toleranter
            if score >= min_score:
                candidates.append({
                    "type": "team_fuzzy",
                    "id_a": rows[i]["id"], "name_a": rows[i]["name"],
                    "id_b": rows[j]["id"], "name_b": rows[j]["name"],
                    "score": score,
                })
    candidates.sort(key=lambda c: -c["score"])
    return candidates


def merge_teams(keep_id: str, merge_id: str, also_to_alt_names: bool = True) -> dict[str, int]:
    """Wie merge_players, aber für Teams.

    Hängt alle games (home + away), team_seasons, player_seasons, coach_tenures,
    playoff_series (team_a + team_b) um.
    Optional: alter Team-Name landet in keep_id.alt_names[] zur Nachvollziehbarkeit.
    """
    merge_name_row = exec_sql(f"SELECT name FROM falken.teams WHERE id = '{merge_id}'")
    if not merge_name_row:
        return {"error": "merge_id not found"}
    merge_name = merge_name_row[0]["name"]
    moved = {"games_home": 0, "games_away": 0, "team_seasons": 0,
             "player_seasons": 0, "coach_tenures": 0,
             "playoff_a": 0, "playoff_b": 0, "playoff_winner": 0}

    sb = supabase()
    # games
    moved["games_home"] = len(exec_sql(f"SELECT id FROM falken.games WHERE home_team_id='{merge_id}'"))
    moved["games_away"] = len(exec_sql(f"SELECT id FROM falken.games WHERE away_team_id='{merge_id}'"))
    sb.table("falken_games").update({"home_team_id": keep_id}).eq("home_team_id", merge_id).execute()
    sb.table("falken_games").update({"away_team_id": keep_id}).eq("away_team_id", merge_id).execute()
    # team_seasons: könnte auf einen Konflikt führen wenn keep_id schon einen Eintrag in der gleichen Saison hat — wir löschen vor merge_id-Eintrag
    ts_old = exec_sql(f"SELECT season_id FROM falken.team_seasons WHERE team_id='{merge_id}'")
    for row in ts_old:
        sid = row["season_id"]
        keep_ts = exec_sql(f"SELECT 1 FROM falken.team_seasons WHERE team_id='{keep_id}' AND season_id='{sid}'")
        if keep_ts:
            sb.table("falken_team_seasons").delete().eq("team_id", merge_id).eq("season_id", sid).execute()
        else:
            sb.table("falken_team_seasons").update({"team_id": keep_id}).eq("team_id", merge_id).eq("season_id", sid).execute()
        moved["team_seasons"] += 1
    # player_seasons, coach_tenures, playoff_series
    sb.table("falken_player_seasons").update({"team_id": keep_id}).eq("team_id", merge_id).execute()
    sb.table("falken_coach_tenures").update({"team_id": keep_id}).eq("team_id", merge_id).execute()
    sb.table("falken_playoff_series").update({"team_a_id": keep_id}).eq("team_a_id", merge_id).execute()
    sb.table("falken_playoff_series").update({"team_b_id": keep_id}).eq("team_b_id", merge_id).execute()
    sb.table("falken_playoff_series").update({"winner_team_id": keep_id}).eq("winner_team_id", merge_id).execute()

    # alt_name beim Keep-Team ergänzen
    if also_to_alt_names:
        keep_row = exec_sql(f"SELECT alt_names FROM falken.teams WHERE id='{keep_id}'")
        if keep_row:
            existing = keep_row[0].get("alt_names") or []
            if merge_name not in existing:
                existing.append(merge_name)
                sb.table("falken_teams").update({"alt_names": existing}).eq("id", keep_id).execute()

    # Lösche merge_id
    sb.table("falken_teams").delete().eq("id", merge_id).execute()
    return moved


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "teams":
        cands = find_duplicate_teams_in_db()
        print(f"\n=== {len(cands)} Team-Duplikat-Kandidaten ===")
        for c in cands[:40]:
            print(f"  [score={c['score']:>3}] '{c['name_a']}' vs '{c['name_b']}'")
    else:
        cands = find_duplicate_players_in_db()
        print(f"\n=== {len(cands)} Player-Duplikat-Kandidaten ===")
        for c in cands[:20]:
            print(f"  [{c['type']:<22} score={c['score']:>3}] '{c['name_a']}' vs '{c['name_b']}'")
        if not cands:
            print("  (keine Player-Duplikate gefunden)")
