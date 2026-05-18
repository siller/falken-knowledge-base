"""EliteProspects-Scraper für historische Falken-Saisons.

URL-Pattern: https://www.eliteprospects.com/team/444/heilbronner-falken/stats/{label}
            Label-Format: "2022-2023" (mit Bindestrich + voller Jahreszahl)

Tabellen auf der Seite:
- "Player Stats" — Feldspieler mit GP, G, A, P, PIM, +/-
- "Goalie Stats" — Torhüter mit GP, W, L, GAA, SV%
- (außerdem Stats anderer Spielzeiten weiter unten)

ToS-Hinweis: EliteProspects hat aggressives Anti-Scraping. Höflich + langsam:
3s + Jitter zwischen Requests. Bei 403/429 stop und manuell prüfen.
"""
from __future__ import annotations

import logging
import re
from typing import Any

from bs4 import BeautifulSoup

from ._base import Scraper

logger = logging.getLogger(__name__)


FALKEN_TEAM_ID_EP = 444
STATS_URL = "https://www.eliteprospects.com/team/{team_id}/heilbronner-falken/stats/{label}"


class EliteProspectsScraper(Scraper):
    source = "elite_prospects"
    rate_limit_sec = 3.5
    rate_jitter_sec = 1.0
    use_proxy = True   # ggf. VPN-Pool nutzen — siehe .env


def label_for_url(label: str) -> str:
    """'2022/23' → '2022-2023'."""
    m = re.match(r"(\d{4})/(\d{2})", label)
    if not m:
        return label
    start = m.group(1)
    end_short = m.group(2)
    end_full = f"{start[0:2]}{end_short}"  # Annahme: gleicher Jahrhundert
    return f"{start}-{end_full}"


async def fetch_season_stats(season_label: str) -> dict[str, Any]:
    """Holt die Stats-Seite für eine Saison, parsed die Player + Goalie Tables.

    Output:
    {
      'season': '2022/23',
      'url': '...',
      'players': [
        {'name': ..., 'position': ..., 'gp': ..., 'goals': ..., 'assists': ..., 'points': ..., 'pim': ..., 'plus_minus': ...},
        ...
      ],
      'goalies': [
        {'name': ..., 'gp': ..., 'wins': ..., 'losses': ..., 'gaa': ..., 'sv_pct': ...},
        ...
      ]
    }
    """
    url_label = label_for_url(season_label)
    url = STATS_URL.format(team_id=FALKEN_TEAM_ID_EP, label=url_label)

    async with EliteProspectsScraper() as s:
        html = await s.get(url)

    soup = BeautifulSoup(html, "lxml")
    players: list[dict[str, Any]] = []
    goalies: list[dict[str, Any]] = []

    # EliteProspects-Tabellen klassifizieren über die Header
    for table in soup.find_all("table"):
        headers = [th.get_text(strip=True) for th in table.find_all("th")]
        if not headers:
            continue
        h_upper = [h.upper() for h in headers]
        header_text = " ".join(h_upper)

        # Feldspieler-Table: "# Player GP G A TP PPG PIM +/-"
        is_player_table = "GP" in h_upper and "G" in h_upper and "A" in h_upper and ("TP" in h_upper or "P" in h_upper) and "+/-" in header_text
        # Torhüter: "# Player GP MIN GAA SV%" oder ähnlich
        is_goalie_table = "GP" in h_upper and ("GAA" in h_upper or "SV%" in h_upper or "SVS%" in h_upper) and "+/-" not in header_text

        if is_player_table:
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) < 8: continue
                name_link = tr.find("a", href=re.compile(r"/player/"))
                if not name_link: continue
                raw_name = name_link.get_text(strip=True)
                # "Alex Tonge(C/LW)" → Name + Position
                m = re.match(r"^(.+?)\s*\(([^)]+)\)$", raw_name)
                if m:
                    name, position_raw = m.group(1).strip(), m.group(2).strip()
                    primary_pos = position_raw.split("/")[0]
                else:
                    name, primary_pos = raw_name, None
                players.append(_parse_player_row(headers, cells, name, primary_pos, name_link.get("href", "")))

        elif is_goalie_table:
            for tr in table.find_all("tr"):
                cells = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cells) < 5: continue
                name_link = tr.find("a", href=re.compile(r"/player/"))
                if not name_link: continue
                goalies.append(_parse_goalie_row(headers, cells, name_link.get_text(strip=True), name_link.get("href", "")))

    return {
        "season": season_label,
        "url": url,
        "players": players,
        "goalies": goalies,
        "html_size": len(html),
    }


def _parse_player_row(headers: list[str], cells: list[str], name: str, position: str | None, url: str) -> dict[str, Any]:
    """Mapped Cells anhand der Header-Reihenfolge."""
    row: dict[str, Any] = {"name": name, "position": position, "ep_url": url}
    h_lower = [h.lower() for h in headers]
    # Erste Spalte ist meist "#" (Rank) — wir filtern später beim Zugriff
    # Cells haben gleiche Länge wie Headers (mit ggf. anderen leeren Spalten)
    for i, h in enumerate(h_lower):
        if i >= len(cells): break
        val = cells[i]
        if h == "gp": row["games_played"] = _int(val)
        elif h == "g": row["goals"] = _int(val)
        elif h == "a": row["assists"] = _int(val)
        elif h in ("tp", "p"): row["points"] = _int(val)
        elif h == "pim": row["pim"] = _int(val)
        elif h == "+/-": row["plus_minus"] = _int(val)
        elif h == "ppg": row["ppg_per_game"] = _float(val)  # Points-Per-Game in EP, NICHT Powerplay-Goals
    return row


def _parse_goalie_row(headers: list[str], cells: list[str], name: str, url: str) -> dict[str, Any]:
    row: dict[str, Any] = {"name": name, "ep_url": url}
    h_lower = [h.lower() for h in headers]
    for i, h in enumerate(h_lower):
        if i >= len(cells): break
        val = cells[i]
        if h == "gp": row["games_played"] = _int(val)
        elif h == "w": row["wins"] = _int(val)
        elif h == "l": row["losses"] = _int(val)
        elif h == "gaa": row["gaa"] = _float(val)
        elif h in ("sv%", "svs%"): row["save_pct"] = _float(val.rstrip("%")) / (100 if val.endswith("%") else 1)
        elif h == "so": row["shutouts"] = _int(val)
        elif h == "min": row["minutes_played"] = _int(val.replace(",", ""))
    return row


def _int(v: str) -> int | None:
    try: return int(v.replace(",", "").replace("-", "0") if v.strip() in ("", "-") else v.replace(",", ""))
    except (ValueError, TypeError): return None


def _float(v: str) -> float | None:
    try: return float(v.replace(",", "."))
    except (ValueError, TypeError): return None


if __name__ == "__main__":
    import asyncio, json
    from ...logging_setup import setup_logging
    setup_logging()
    res = asyncio.run(fetch_season_stats("2022/23"))
    print(f"\nSaison: {res['season']}")
    print(f"URL: {res['url']}")
    print(f"HTML-Größe: {res['html_size']} bytes")
    print(f"Players: {len(res['players'])}")
    print(f"Goalies: {len(res['goalies'])}")
    if res['players']:
        print(f"\nErste 3 Players:")
        for p in res['players'][:3]:
            print(f"  {p['name']} — {p['raw_cells']}")
    if res['goalies']:
        print(f"\nErste 2 Goalies:")
        for g in res['goalies'][:2]:
            print(f"  {g['name']} — {g['raw_cells']}")
