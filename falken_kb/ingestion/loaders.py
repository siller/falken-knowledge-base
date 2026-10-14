"""Loader: hockeydata-Responses → Supabase via REST/RPC.

Nutzt die Upsert-RPCs aus migration 0003_rpcs.sql (kein direkter Postgres-Connect nötig).
"""
from __future__ import annotations

import logging
import unicodedata
from typing import Any

from ..db import _with_retry, exec_sql, rpc, supabase
from .hockeydata_client import HockeydataClient

logger = logging.getLogger(__name__)


def upsert_season(label: str, league: str, league_tier: int, hockeydata_season_id: int) -> str:
    """Upsert Season, return UUID."""
    return rpc("upsert_season", {
        "p_label": label,
        "p_league": league,
        "p_league_tier": league_tier,
        "p_hockeydata_id": str(hockeydata_season_id),
    })


# Name → kanonischer Teamname (oder None), je Prozess einmal nachgeschlagen.
_ALIAS_CACHE: dict[str, str | None] = {}


def _kanonischer_teamname(name: str) -> str:
    """Löst bekannte Schreibweisen (teams.alt_names) auf das kanonische Team auf.

    WHY: hockeydata führt die Falken ab 2026/27 als "Heilbronner EC Falken".
    Ohne Auflösung entstand jeden Tag ein neues Team, und der Merge danach
    verwarf dessen frische Tabellenzeile zugunsten der alten mit 0 Spielen.
    """
    if name not in _ALIAS_CACHE:
        res = _with_retry(lambda: supabase().table("falken_teams").select("name")
                          .contains("alt_names", [name]).limit(1).execute())
        _ALIAS_CACHE[name] = res.data[0]["name"] if res.data else None
    return _ALIAS_CACHE[name] or name


def upsert_team(name: str, short_name: str | None = None, hockeydata_team_id: int | None = None) -> str:
    return rpc("upsert_team", {
        "p_name": _kanonischer_teamname(name),
        "p_short_name": short_name,
        "p_hockeydata_id": str(hockeydata_team_id) if hockeydata_team_id is not None else None,
    })


def _pick(d: dict, *keys: str) -> Any:
    """Hockeydata-API ist inkonsistent: teamLongname (lowercase) in Standings,
    homeTeamLongName (CamelCase) im Schedule. Probiere alle Varianten."""
    for k in keys:
        v = d.get(k)
        if v is not None:
            return v
    return None


def upsert_team_seasons_from_standings(season_id: str, standings_rows: list[dict[str, Any]]) -> int:
    count = 0
    for row in standings_rows:
        name = _pick(row, "teamLongname", "teamLongName", "teamShortname", "teamShortName")
        if not name:
            logger.warning("Standings-Row ohne Team-Namen, skip: %s", str(row)[:120])
            continue
        team_uuid = upsert_team(
            name=name,
            short_name=_pick(row, "teamShortname", "teamShortName"),
            hockeydata_team_id=row.get("id"),
        )
        # Vor dem ersten Spieltag liefert hockeydata für jedes Team Rang 1 bei
        # 0 Spielen. Als final_rank gespeichert stünde damit die halbe Liga auf
        # Platz 1 — also Rang erst übernehmen, wenn gespielt wurde.
        rank = row.get("tableRank")
        if not row.get("gamesPlayed"):
            rank = None

        rpc("upsert_team_season", {
            "p_team_id": team_uuid,
            "p_season_id": season_id,
            "p_rank": rank,
            "p_gp": row.get("gamesPlayed"),
            "p_wins": row.get("gamesWon"),
            "p_losses": row.get("gamesLost"),
            "p_ot_wins": row.get("gamesWonInOt"),
            "p_ot_losses": row.get("gamesLostInOt"),
            "p_points": row.get("points"),
            "p_gf": row.get("goalsFor"),
            "p_ga": row.get("goalsAgainst"),
            "p_hd_id": str(row.get("id")) if row.get("id") is not None else None,
        })
        count += 1
    return count


def upsert_games_from_schedule(season_id: str, schedule_rows: list[dict[str, Any]], game_type: str = "regular") -> int:
    count = 0
    skipped = 0
    for m in schedule_rows:
        home_name = _pick(m, "homeTeamLongName", "homeTeamLongname", "homeTeamShortName", "homeTeamShortname")
        away_name = _pick(m, "awayTeamLongName", "awayTeamLongname", "awayTeamShortName", "awayTeamShortname")
        if not home_name or not away_name:
            skipped += 1
            continue
        home_uuid = upsert_team(
            name=home_name,
            short_name=_pick(m, "homeTeamShortName", "homeTeamShortname"),
            hockeydata_team_id=m.get("homeTeamId"),
        )
        away_uuid = upsert_team(
            name=away_name,
            short_name=_pick(m, "awayTeamShortName", "awayTeamShortname"),
            hockeydata_team_id=m.get("awayTeamId"),
        )
        # scheduledGameStart ist im ISO-Format; scheduledDate ist nur das Datum (oft Dict)
        sched_iso = m.get("scheduledGameStart")
        if not sched_iso:
            sched = m.get("scheduledDate")
            if isinstance(sched, dict):
                sched_iso = sched.get("value") or sched.get("formattedLong")
            else:
                sched_iso = sched
        if not sched_iso:
            skipped += 1
            continue
        # ACHTUNG: hockeydata liefert für noch nicht gespielte Partien
        # homeTeamScore=0/awayTeamScore=0 statt null — erkennbar nur an
        # gameStatus (0 = angesetzt, 4 = beendet). Ungeprüft übernommen
        # landen ganze Spielpläne als 0:0-Ergebnisse in der DB. Laufende
        # Partien (1-3) hätten sonst ihren Zwischenstand als Endergebnis.
        home_score = m.get("homeTeamScore")
        away_score = m.get("awayTeamScore")
        status = m.get("gameStatus")
        if status is not None and status != 4 and not m.get("gameHasEnded"):
            home_score = away_score = None

        # Der Schedule meldet isOvertime/isShootOut; scoreInfo bleibt als
        # Rückfall für ältere Antworten.
        overtime = bool(m.get("isOvertime") or m.get("scoreInfo") in ("OT", "OTW", "OTL"))
        shootout = bool(m.get("isShootOut") or m.get("scoreInfo") in ("SO", "SOW", "SOL"))
        hd_id = str(m.get("id")) if m.get("id") else None
        rpc("upsert_game", {
            "p_season_id": season_id,
            "p_date": sched_iso,
            "p_game_type": game_type,
            "p_home_team_id": home_uuid,
            "p_away_team_id": away_uuid,
            "p_home_score": home_score,
            "p_away_score": away_score,
            "p_overtime": overtime,
            "p_shootout": shootout,
            "p_hd_id": hd_id,
        })
        # upsert_game fügt nur ein — eine im Juli ohne Ergebnis angelegte Partie
        # bekäme ihr Ergebnis sonst nie. Termin immer nachziehen (Verlegungen),
        # das Ergebnis nur von beendeten Partien: ein angesetztes Spiel darf ein
        # vorhandenes Ergebnis nicht wieder löschen.
        if hd_id:
            nachtrag: dict[str, Any] = {"date": sched_iso}
            if home_score is not None and away_score is not None:
                nachtrag.update(home_score=home_score, away_score=away_score,
                                overtime=overtime, shootout=shootout)
            _with_retry(lambda d=nachtrag, h=hd_id: supabase().table("falken_games").update(d)
                        .eq("source_ids->>hockeydata", h).execute())
        # upsert_game gibt einen boolean zurück, der zwischen supabase-py-Versionen
        # unterschiedlich serialisiert wird. Wir zählen schlicht alle attempts;
        # echte Duplikate werden im SQL (WHERE NOT EXISTS) erkannt und ignoriert.
        count += 1
    if skipped:
        logger.info("  %d Spiele übersprungen (fehlende Teamdaten/Datum)", skipped)
    return count


def falken_team_ids(standings_rows: list[dict[str, Any]]) -> set[int]:
    """teamIds der Falken in einer hockeydata-Tabelle.

    hockeydata vergibt die teamId pro Saison neu (47011 bis 2025/26, 70543 ab
    2026/27) — deshalb aus der Tabelle ableiten statt fest verdrahten.
    """
    ids = set()
    for row in standings_rows:
        name = _pick(row, "teamLongname", "teamLongName") or ""
        if "Heilbronn" in name and "Falken" in name and row.get("id") is not None:
            ids.add(int(row["id"]))
    return ids


_UMSCHRIFT = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})

# hockeydata-eigene Positionskürzel → Schreibweise, die die DB schon kennt.
_POSITIONEN = {"LD": "D", "RD": "D", "LF": "F", "RF": "F"}


def _namensschluessel(name: str, umschrift: bool = False) -> str:
    """"Frédérik Cabana" und "Frederik CABANA" ergeben denselben Schlüssel.

    Mit `umschrift` wird aus "Müller" "mueller", ohne "muller" — hockeydata
    schreibt Umlaute mal so, mal so, deshalb gleicht der Loader beide ab.
    """
    text = unicodedata.normalize("NFC", name).casefold()
    if umschrift:
        text = text.translate(_UMSCHRIFT)
    ohne_akzente = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return " ".join(ohne_akzente.split())


def _schluessel(name: str) -> set[str]:
    return {_namensschluessel(name), _namensschluessel(name, umschrift=True)}


def _anzeigename(vorname: str, nachname: str) -> str:
    """hockeydata schreibt Nachnamen groß: "MÜLLER-WEST" -> "Müller-West"."""
    def wort(w: str) -> str:
        return "-".join(t.capitalize() for t in w.split("-")) if w.isupper() and len(w) > 1 else w
    return " ".join(wort(w) for w in f"{vorname} {nachname}".split())


def _kurzform_treffer(schluessel: str, kader: dict[str, str]) -> str | None:
    """"christopher schutz" trifft "chris schutz" — aber nur, wenn eindeutig.

    hockeydata führt den vollen Vornamen, EliteProspects oft die Kurzform.
    """
    vorname, _, nachname = schluessel.rpartition(" ")
    treffer = {
        ps_id for k, ps_id in kader.items()
        if k.rpartition(" ")[2] == nachname
        and (k.rpartition(" ")[0].startswith(vorname) or vorname.startswith(k.rpartition(" ")[0]))
    }
    # Menge: beide Schlüssel-Varianten eines Spielers zeigen auf dieselbe ID.
    return next(iter(treffer)) if len(treffer) == 1 and vorname else None


def upsert_skater_stats_from_leaders(
    season_id: str, team_id: str, leader_rows: list[dict[str, Any]], falken_ids: set[int],
) -> int:
    """Feldspieler-Statistik der Falken (hockeydata LeaderFieldPlayers) → player_stats.

    Abgleich ohne Akzente und Groß-/Kleinschreibung: erst gegen den Kader der
    Saison (von EliteProspects angelegt), dann gegen alle bekannten Spieler,
    sonst wird der Spieler neu angelegt.
    """
    zeilen = [r for r in leader_rows if r.get("teamId") is not None and int(r["teamId"]) in falken_ids]
    if not zeilen:
        return 0

    kader = {
        k: r["ps_id"]
        for r in exec_sql(
            "SELECT ps.id AS ps_id, p.id AS player_id, p.name FROM falken.player_seasons ps "
            "JOIN falken.players p ON p.id = ps.player_id "
            f"WHERE ps.season_id = '{season_id}' AND ps.team_id = '{team_id}'"
        )
        for k in _schluessel(r["name"])
    }
    alle_spieler: dict[str, str] | None = None

    n = 0
    for r in zeilen:
        name = _anzeigename(r.get("playerFirstname") or "", r.get("playerLastname") or "")
        if not name:
            continue
        schluessel = _namensschluessel(name)
        varianten = _schluessel(name)
        ps_id = (next((kader[k] for k in varianten if k in kader), None)
                 or _kurzform_treffer(schluessel, kader))
        if ps_id is None:
            if alle_spieler is None:
                alle_spieler = {k: p["id"] for p in exec_sql("SELECT id, name FROM falken.players")
                                for k in _schluessel(p["name"])}
            player_id = next((alle_spieler[k] for k in varianten if k in alle_spieler), None)
            if player_id is None:
                pos = r.get("position")
                neu = {"name": name, "position": _POSITIONEN.get(pos, pos),
                       "source_ids": {"hockeydata": str(r.get("id"))}}
                player_id = _with_retry(
                    lambda d=neu: supabase().table("falken_players").insert(d).execute()).data[0]["id"]
                alle_spieler.update(dict.fromkeys(varianten, player_id))
            zuordnung = {"player_id": player_id, "team_id": team_id, "season_id": season_id,
                         "jersey_number": r.get("playerJerseyNr"), "source_ids": {"hockeydata": True}}
            ps_id = _with_retry(
                lambda d=zuordnung: supabase().table("falken_player_seasons").insert(d).execute()).data[0]["id"]
            kader.update(dict.fromkeys(varianten, ps_id))

        # points ist eine GENERATED Column (goals + assists) — nicht mitschicken.
        stats = {
            "player_season_id": ps_id,
            "games_played": r.get("gamesPlayed"),
            "goals": r.get("goals"),
            "assists": r.get("assists"),
            "pim": r.get("penaltyMinutes"),
            "plus_minus": r.get("plusMinus"),
            "ppg": r.get("powerplayGoals"),
            "shg": r.get("shorthandedGoals"),
            "gwg": r.get("gameWinningGoals"),
            "shots": r.get("shotsOnGoal"),
        }
        _with_retry(lambda d=stats: supabase().table("falken_player_stats")
                    .upsert(d, on_conflict="player_season_id").execute())
        n += 1
    return n


# Ab wann der tägliche Sync rot wird. Einzelne Nachzügler (Ergebnis noch nicht
# freigegeben, Spielverlegung) sind normal, eine ganze Spielwoche nicht.
MAX_OFFENE_ERGEBNISSE = 3
MAX_FALKEN_RUECKSTAND = 2


def aktualitaets_probleme(offene_ergebnisse: int, falken_spiele: int | None, max_spiele: int | None) -> list[str]:
    """Was am Datenstand der laufenden Saison nicht stimmt — leer heißt: alles gut.

    WHY: Bis Oktober 2026 meldete der Sync jeden Tag "ohne Fehler", während
    die Saison 2026/27 ohne ein einziges Ergebnis in der DB stand.
    """
    probleme = []
    if offene_ergebnisse > MAX_OFFENE_ERGEBNISSE:
        probleme.append(f"{offene_ergebnisse} vergangene Ligaspiele der laufenden Saison ohne Ergebnis")
    if max_spiele and (falken_spiele or 0) + MAX_FALKEN_RUECKSTAND < max_spiele:
        probleme.append(f"Falken-Tabellenzeile steht bei {falken_spiele or 0} Spielen, die Liga bei {max_spiele}")
    return probleme


async def load_current_season(league_id: int, league_name: str, league_tier: int, division_id: int) -> dict[str, int]:
    """Komplett-Load einer Saison: Tabelle + Spielplan."""
    async with HockeydataClient() as c:
        seasons = await c.get_seasons(league_id)
        current = seasons[-1] if seasons else None
        if not current:
            raise RuntimeError(f"Keine Saisons für leagueId={league_id}")

        season_label = current["seasonName"].replace("Saison ", "")
        season_uuid = upsert_season(season_label, league_name, league_tier, current["seasonId"])

        standings = await c.get_standings(division_id)
        n_teams = upsert_team_seasons_from_standings(season_uuid, standings)

        schedule = await c.get_schedule(division_id)
        n_games = upsert_games_from_schedule(season_uuid, schedule)

        return {"season_uuid": season_uuid, "n_teams": n_teams, "n_games": n_games}
