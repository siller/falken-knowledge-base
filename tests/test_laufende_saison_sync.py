"""Täglicher Sync der laufenden Saison.

WHY: Im Oktober 2026 nannte HORST auf "Wer ist der aktuelle Topscorer?" Calder
Anderson aus 2025/26. Die DB hatte für 2026/27 kein einziges Ergebnis, die
Falken standen mit 0 Spielen in der Tabelle, Spielerpunkte fehlten ganz — und
der Sync meldete trotzdem jeden Tag "✓ ohne Fehler". Vier Ursachen:

1. upsert_game fügte nur ein: der Spielplan kam im Juli ohne Ergebnisse, jeder
   spätere Lauf übersprang die bekannten Partien.
2. hockeydata führt den Klub als "Heilbronner EC Falken". Der Sync legte dafür
   täglich ein neues Team an, der Merge danach verwarf dessen frische
   Tabellenzeile zugunsten der alten mit 0 Spielen.
3. Spielerstatistiken der laufenden Saison lud niemand.
4. Der Aktualitätsbericht zeigte das Problem, schlug aber nicht an.
"""
from __future__ import annotations

from typing import Any

import pytest

from falken_kb.ingestion import loaders


class _Abfrage:
    """Minimaler Ersatz für die PostgREST-Kette supabase().table(...)…execute()."""

    def __init__(self, tabelle: str, log: list, antworten: dict):
        self.tabelle, self.log, self.antworten = tabelle, log, antworten
        self.op: tuple[str, Any] | None = None
        self.filter: list[tuple] = []

    def update(self, daten):
        self.op = ("update", daten)
        return self

    def upsert(self, daten, on_conflict=None):
        self.op = ("upsert", daten, on_conflict)
        return self

    def insert(self, daten):
        self.op = ("insert", daten)
        return self

    def select(self, *_):
        self.op = ("select",)
        return self

    def eq(self, spalte, wert):
        self.filter.append(("eq", spalte, wert))
        return self

    def contains(self, spalte, wert):
        self.filter.append(("contains", spalte, wert))
        return self

    def limit(self, _):
        return self

    def execute(self):
        self.log.append((self.tabelle, self.op, self.filter))
        daten = self.antworten.get((self.tabelle, self.op[0]), [])
        return type("Antwort", (), {"data": daten(self) if callable(daten) else daten})()


class _Supabase:
    def __init__(self, antworten: dict | None = None):
        self.log: list = []
        self.antworten = antworten or {}

    def table(self, name):
        return _Abfrage(name, self.log, self.antworten)


@pytest.fixture
def db(monkeypatch):
    sb = _Supabase()
    rpcs: list[tuple[str, dict]] = []

    def fake_rpc(name, params):
        rpcs.append((name, params))
        return f"uuid-{params.get('p_name', name)}"

    monkeypatch.setattr(loaders, "supabase", lambda: sb)
    monkeypatch.setattr(loaders, "rpc", fake_rpc)
    loaders._ALIAS_CACHE.clear()
    return sb, rpcs


def _spiel(**ueber):
    m = {
        "id": "hd-1", "homeTeamLongName": "Deggendorfer SC", "awayTeamLongName": "Tölzer Löwen",
        "scheduledGameStart": "2026-10-10T19:30:00+02:00",
        "homeTeamScore": 4, "awayTeamScore": 2, "gameStatus": 4,
        "isOvertime": False, "isShootOut": False,
    }
    m.update(ueber)
    return m


def _updates(sb):
    return [e for e in sb.log if e[0] == "falken_games" and e[1][0] == "update"]


# ── 1. Ergebnisse nachtragen ────────────────────────────────────────────────

def test_beendetes_spiel_traegt_ergebnis_in_bestehende_partie_nach(db):
    sb, _ = db
    loaders.upsert_games_from_schedule("saison-1", [_spiel()])

    updates = _updates(sb)
    assert len(updates) == 1, "bekannte Partie muss ihr Ergebnis nachgetragen bekommen"
    _, (_, daten), filter_ = updates[0]
    assert daten["home_score"] == 4 and daten["away_score"] == 2
    assert daten["date"] == "2026-10-10T19:30:00+02:00"
    assert ("eq", "source_ids->>hockeydata", "hd-1") in filter_


def test_angesetztes_spiel_loescht_kein_ergebnis_aber_verlegt_den_termin(db):
    """hockeydata liefert für angesetzte Partien 0:0 — das darf nie als Ergebnis landen."""
    sb, _ = db
    loaders.upsert_games_from_schedule("saison-1", [_spiel(gameStatus=0, homeTeamScore=0, awayTeamScore=0)])

    (_, (_, daten), _), = _updates(sb)
    assert "home_score" not in daten and "away_score" not in daten
    assert daten["date"] == "2026-10-10T19:30:00+02:00"


def test_verlaengerung_und_penaltyschiessen_werden_nachgetragen(db):
    """hockeydata meldet beides als isOvertime/isShootOut — scoreInfo gibt es nicht."""
    sb, _ = db
    loaders.upsert_games_from_schedule("saison-1", [_spiel(isOvertime=True, isShootOut=True)])
    (_, (_, daten), _), = _updates(sb)
    assert daten["shootout"] is True and daten["overtime"] is True


@pytest.mark.parametrize("status", [1, 2, 3])
def test_laufendes_spiel_schreibt_keinen_zwischenstand_als_ergebnis(db, status):
    sb, rpcs = db
    loaders.upsert_games_from_schedule("saison-1", [_spiel(gameStatus=status)])
    (_, (_, daten), _), = _updates(sb)
    assert "home_score" not in daten
    (params,) = [p for n, p in rpcs if n == "upsert_game"]
    assert params["p_home_score"] is None and params["p_away_score"] is None


def test_einzelner_verbindungsabbruch_kostet_kein_ergebnis(db, monkeypatch):
    """Rund 400 Einzel-Requests pro Lauf — ein HTTP/2-Flake darf den Schritt nicht abbrechen."""
    import httpx

    from falken_kb import db as db_modul

    sb, _ = db
    monkeypatch.setattr(db_modul, "_reset_client", lambda: None)
    monkeypatch.setattr(db_modul.time, "sleep", lambda _: None)
    fehler = iter([httpx.RemoteProtocolError("flake")])

    def einmal_fehlschlagen(q):
        if q.op[0] == "update" and (e := next(fehler, None)):
            raise e
        return []
    sb.antworten[("falken_games", "update")] = einmal_fehlschlagen

    loaders.upsert_games_from_schedule("saison-1", [_spiel()])
    assert len(_updates(sb)) == 2, "nach dem Flake muss der Update wiederholt werden"


def test_spiel_ohne_hockeydata_id_wird_nicht_blind_aktualisiert(db):
    sb, _ = db
    loaders.upsert_games_from_schedule("saison-1", [_spiel(id=None)])
    assert _updates(sb) == []


# ── 2. Team-Aliasse ──────────────────────────────────────────────────────────

def test_alias_wird_auf_das_kanonische_team_aufgeloest(db):
    sb, rpcs = db
    sb.antworten[("falken_teams", "select")] = lambda q: (
        [{"name": "Heilbronner Falken"}]
        if ("contains", "alt_names", ["Heilbronner EC Falken"]) in q.filter else []
    )
    loaders.upsert_team("Heilbronner EC Falken", "HEF", hockeydata_team_id=70543)

    (name, params), = rpcs
    assert name == "upsert_team"
    assert params["p_name"] == "Heilbronner Falken", "sonst entsteht täglich ein Duplikat-Team"
    assert params["p_hockeydata_id"] == "70543"


def test_unbekannter_name_bleibt_unveraendert(db):
    _, rpcs = db
    loaders.upsert_team("EC Peiting", "PEI", hockeydata_team_id=13063)
    assert rpcs[0][1]["p_name"] == "EC Peiting"


# ── 3. Spielerstatistik ──────────────────────────────────────────────────────

def _scorer(vor, nach, team=70543, **ueber):
    r = {"id": f"{vor}-{nach}", "playerFirstname": vor, "playerLastname": nach, "teamId": team,
         "position": "C", "gamesPlayed": 9, "goals": 9, "assists": 8, "points": 17,
         "penaltyMinutes": 4, "plusMinus": 3, "powerplayGoals": 2, "shorthandedGoals": 0,
         "gameWinningGoals": 1, "shotsOnGoal": 30}
    r.update(ueber)
    return r


def test_scorer_wird_dem_kaderspieler_trotz_akzent_und_grossschreibung_zugeordnet(db, monkeypatch):
    sb, _ = db
    monkeypatch.setattr(loaders, "exec_sql", lambda q: (
        [{"ps_id": "ps-cabana", "player_id": "p-cabana", "name": "Frédérik Cabana"}]
        if "player_seasons" in q else [{"id": "p-cabana", "name": "Frédérik Cabana"}]
    ))
    n = loaders.upsert_skater_stats_from_leaders("saison", "team", [_scorer("Frederik", "CABANA")], {70543})

    assert n == 1
    (_, (op, daten, konflikt), _), = [e for e in sb.log if e[0] == "falken_player_stats"]
    assert op == "upsert" and konflikt == "player_season_id"
    assert daten["player_season_id"] == "ps-cabana"
    assert (daten["games_played"], daten["goals"], daten["assists"]) == (9, 9, 8)
    assert "points" not in daten, "points ist eine GENERATED Column"
    assert not [e for e in sb.log if e[0] == "falken_players"], "kein Duplikat-Spieler anlegen"


@pytest.mark.parametrize("kader,erwartet", [
    (["Chris Schutz", "Anton Seewald"], "ps-0"),        # Kurzform des Vornamens
    (["Chris Schutz", "Christoph Schutz"], None),         # nicht eindeutig → neu anlegen
    (["Max Schutz"], None),                               # anderer Vorname → neu anlegen
])
def test_kurzform_des_vornamens_trifft_den_kaderspieler_nur_eindeutig(db, monkeypatch, kader, erwartet):
    sb, _ = db
    monkeypatch.setattr(loaders, "exec_sql", lambda q: (
        [{"ps_id": f"ps-{i}", "player_id": f"p-{i}", "name": n} for i, n in enumerate(kader)]
        if "player_seasons" in q else []
    ))
    sb.antworten[("falken_players", "insert")] = [{"id": "p-neu"}]
    sb.antworten[("falken_player_seasons", "insert")] = [{"id": "ps-neu"}]

    loaders.upsert_skater_stats_from_leaders("saison", "team", [_scorer("Christopher", "SCHUTZ")], {70543})

    (_, (_, stats, _), _), = [e for e in sb.log if e[0] == "falken_player_stats"]
    assert stats["player_season_id"] == (erwartet or "ps-neu")


def test_fremde_spieler_werden_ignoriert(db, monkeypatch):
    sb, _ = db
    monkeypatch.setattr(loaders, "exec_sql", lambda q: [])
    n = loaders.upsert_skater_stats_from_leaders("saison", "team", [_scorer("Max", "FREMD", team=20912)], {70543})
    assert n == 0 and sb.log == []


def test_spieler_ohne_kadereintrag_wird_angelegt(db, monkeypatch):
    sb, _ = db
    monkeypatch.setattr(loaders, "exec_sql", lambda q: [])
    sb.antworten[("falken_players", "insert")] = [{"id": "p-neu"}]
    sb.antworten[("falken_player_seasons", "insert")] = [{"id": "ps-neu"}]

    loaders.upsert_skater_stats_from_leaders("saison", "team", [_scorer("Jan-Ole", "MÜLLER-WEST")], {70543})

    (_, (_, spieler), _), = [e for e in sb.log if e[0] == "falken_players"]
    assert spieler["name"] == "Jan-Ole Müller-West"
    (_, (_, ps), _), = [e for e in sb.log if e[0] == "falken_player_seasons"]
    assert (ps["player_id"], ps["team_id"], ps["season_id"]) == ("p-neu", "team", "saison")
    (_, (_, stats, _), _), = [e for e in sb.log if e[0] == "falken_player_stats"]
    assert stats["player_season_id"] == "ps-neu"


def test_ehemaliger_spieler_wird_wiedererkannt_statt_doppelt_angelegt(db, monkeypatch):
    sb, _ = db
    monkeypatch.setattr(loaders, "exec_sql", lambda q: (
        [] if "player_seasons" in q else [{"id": "p-alt", "name": "Calder ANDERSON"}]
    ))
    sb.antworten[("falken_player_seasons", "insert")] = [{"id": "ps-neu"}]

    loaders.upsert_skater_stats_from_leaders("saison", "team", [_scorer("Calder", "ANDERSON")], {70543})

    assert not [e for e in sb.log if e[0] == "falken_players"]
    (_, (_, ps), _), = [e for e in sb.log if e[0] == "falken_player_seasons"]
    assert ps["player_id"] == "p-alt"


def test_falken_team_ids_kommen_aus_der_tabelle():
    """hockeydata wechselt die teamId jede Saison — nie fest verdrahten."""
    tabelle = [{"id": 20912, "teamLongname": "Deggendorfer SC"},
               {"id": 70543, "teamLongname": "Heilbronner EC Falken"}]
    assert loaders.falken_team_ids(tabelle) == {70543}


# ── 4. Aktualität schlägt an ────────────────────────────────────────────────

def test_aktualitaet_meldet_fehlende_ergebnisse():
    probleme = loaders.aktualitaets_probleme(offene_ergebnisse=63, falken_spiele=9, max_spiele=9)
    assert probleme and "63" in probleme[0]


def test_aktualitaet_meldet_eingefrorene_falken_tabellenzeile():
    probleme = loaders.aktualitaets_probleme(offene_ergebnisse=0, falken_spiele=0, max_spiele=9)
    assert probleme and "Falken" in probleme[0]


def test_aktualitaet_toleriert_einzelne_nachzuegler_und_saisonpause():
    assert loaders.aktualitaets_probleme(offene_ergebnisse=2, falken_spiele=8, max_spiele=9) == []
    assert loaders.aktualitaets_probleme(offene_ergebnisse=0, falken_spiele=None, max_spiele=None) == []


def test_umlaut_umschrift_trifft_den_kaderspieler(db, monkeypatch):
    """hockeydata schreibt mal "MUELLER", EliteProspects "Müller"."""
    sb, _ = db
    monkeypatch.setattr(loaders, "exec_sql", lambda q: (
        [{"ps_id": "ps-mueller", "player_id": "p", "name": "Jonas Müller"}] if "player_seasons" in q else []
    ))
    loaders.upsert_skater_stats_from_leaders("saison", "team", [_scorer("Jonas", "MUELLER")], {70543})
    (_, (_, stats, _), _), = [e for e in sb.log if e[0] == "falken_player_stats"]
    assert stats["player_season_id"] == "ps-mueller"


# Die DB kennt D, F, C, LW, RW, W, G (EliteProspects). Nur hockeydata-eigene
# Kürzel werden übersetzt, sonst stünde "LD" neben 90 Verteidigern mit "D".
@pytest.mark.parametrize("roh,erwartet", [("RF", "F"), ("LF", "F"), ("LD", "D"), ("RD", "D"),
                                          ("C", "C"), ("LW", "LW"), ("D", "D"), (None, None)])
def test_neue_spieler_bekommen_die_positionen_des_schemas(db, monkeypatch, roh, erwartet):
    sb, _ = db
    monkeypatch.setattr(loaders, "exec_sql", lambda q: [])
    sb.antworten[("falken_players", "insert")] = [{"id": "p-neu"}]
    sb.antworten[("falken_player_seasons", "insert")] = [{"id": "ps-neu"}]
    loaders.upsert_skater_stats_from_leaders("saison", "team", [_scorer("Neu", "SPIELER", position=roh)], {70543})
    (_, (_, spieler), _), = [e for e in sb.log if e[0] == "falken_players"]
    assert spieler["position"] == erwartet


@pytest.mark.parametrize("hockeydata,kader", [
    ("MULLER", "Jonas Müller"),                 # Umlaut weggelassen
    ("MUELLER", "Jonas Müller"),                # Umlaut umschrieben
    ("MÜLLER", "Jonas Müller"),           # zerlegtes ü in der DB
])
def test_umlaut_varianten_treffen_denselben_spieler(db, monkeypatch, hockeydata, kader):
    sb, _ = db
    monkeypatch.setattr(loaders, "exec_sql", lambda q: (
        [{"ps_id": "ps-mueller", "player_id": "p", "name": kader}] if "player_seasons" in q else []
    ))
    loaders.upsert_skater_stats_from_leaders("saison", "team", [_scorer("Jonas", hockeydata)], {70543})
    assert not [e for e in sb.log if e[0] == "falken_players"], "kein Duplikat anlegen"
    (_, (_, stats, _), _), = [e for e in sb.log if e[0] == "falken_player_stats"]
    assert stats["player_season_id"] == "ps-mueller"


def test_kurzform_mit_umlaut_bleibt_eindeutig(db, monkeypatch):
    """Beide Schlüssel-Varianten zeigen auf denselben Kadereintrag — das ist kein Zweifelsfall."""
    sb, _ = db
    monkeypatch.setattr(loaders, "exec_sql", lambda q: (
        [{"ps_id": "ps-0", "player_id": "p", "name": "Chris Schütz"}] if "player_seasons" in q else []
    ))
    loaders.upsert_skater_stats_from_leaders("saison", "team", [_scorer("Christopher", "SCHÜTZ")], {70543})
    (_, (_, stats, _), _), = [e for e in sb.log if e[0] == "falken_player_stats"]
    assert stats["player_season_id"] == "ps-0"
