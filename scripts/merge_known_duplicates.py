"""Konsolidiert bekannte Team-Duplikate.

Format pro Merge: (keep_name, [merge_name1, merge_name2, ...])
Der erste Name bleibt erhalten, alle anderen werden hineingemerged.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from falken_kb.db import exec_sql
from falken_kb.ingestion.dedup import merge_teams


MERGES: list[tuple[str, list[str]]] = [
    ("Heilbronner Falken", ["Heibronner EC Falken"]),  # Typo
    ("Bayreuth Tigers", ["EHC Bayreuth Tigers", "onesto Tigers Bayreuth"]),
    ("Tölzer Löwen", ["EC Bad Tölzer Löwen"]),
    ("ECDC Memmingen Indians", ["ECDC Indians Memmingen"]),
    ("EHC Freiburg", ["EHC Wölfe Freiburg"]),
    ("Eispiraten Crimmitschau", ["ETC Eispiraten Crimmitschau", "ETC Crimmitschau"]),
    ("Moskitos Essen", ["ESC Moskitos Essen"]),
    ("ESV Kaufbeuren", ["ESV Kaufbeuren Buron Joker"]),
    ("Lausitzer Füchse", ["Lausitzer Füchse Weisswasser"]),
    ("Selber Wölfe", ["VER Selber Wölfe"]),
    ("StarBulls Rosenheim", ["Starbulls Rosenheim"]),  # Case-Variante
    ("Icefighters Leipzig", ["EXA Icefighters Leipzig", "KSW Icefighters Leipzig"]),  # Sponsor-Wechsel
    ("Schwenninger Wild Wings", ["SERC Wild Wings Schwenningen"]),
    ("Dresdner Eislöwen", ["ESC Eislöwen Dresden"]),
    # 2. Iteration (neue Duplikate aus erweitertem Bulk-Load):
    ("Hannover Indians", ["EC Hannover Indians"]),
    ("EV Lindau Islanders", ["EV Lindau"]),
    ("HC Banik Sokolov", ["HC Sokolov"]),
    # 3. Iteration (older Bulk-Load brachte neue Varianten):
    ("Bayreuth Tigers", ["EHC Bayreuth - Tigers", "onesto Tigers Bayreuth"]),
    ("Icefighters Leipzig", ["KSW Icefighters Leipzig"]),
    ("StarBulls Rosenheim", ["Starbulls Rosenheim"]),
]


def get_id(name: str) -> str | None:
    rows = exec_sql(f"SELECT id FROM falken.teams WHERE name = $${name}$$")
    return rows[0]["id"] if rows else None


def main() -> None:
    print(f"\n=== Konsolidiere {len(MERGES)} Team-Cluster ===")
    total_merges = 0
    total_moves = 0
    for keep_name, merge_list in MERGES:
        keep_id = get_id(keep_name)
        if not keep_id:
            # falls keep_name nicht existiert (z.B. "Icefighters Leipzig" als kanonischer Name),
            # nehmen wir den ersten der merge_list und benennen ihn um
            for m_name in merge_list:
                m_id = get_id(m_name)
                if m_id:
                    print(f"  ⚠️  '{keep_name}' fehlt, nehme '{m_name}' und benenne um")
                    # Update via supabase-py
                    from falken_kb.db import supabase
                    supabase().table("falken_teams").update({"name": keep_name}).eq("id", m_id).execute()
                    keep_id = m_id
                    merge_list = [n for n in merge_list if n != m_name]
                    break
            if not keep_id:
                print(f"  ✗ KEINE Team-ID gefunden für Cluster {keep_name}")
                continue
        for merge_name in merge_list:
            merge_id = get_id(merge_name)
            if not merge_id:
                print(f"    skip: '{merge_name}' nicht in DB")
                continue
            if merge_id == keep_id:
                continue
            try:
                res = merge_teams(keep_id, merge_id, also_to_alt_names=True)
                games_moved = res.get("games_home", 0) + res.get("games_away", 0)
                print(f"  ✓ '{merge_name}' → '{keep_name}' (games={games_moved}, ts={res.get('team_seasons',0)}, players={res.get('player_seasons',0) if 'player_seasons' in res else '-'})")
                total_merges += 1
                total_moves += games_moved
            except Exception as e:
                print(f"    FAIL: {e}")
    print(f"\n=== Total: {total_merges} Merges, {total_moves} games verschoben ===")


if __name__ == "__main__":
    main()
