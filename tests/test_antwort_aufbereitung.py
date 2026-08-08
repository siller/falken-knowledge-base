"""Aufbereitung der DB-Zeilen vor der Synthese.

WHY: Die Antworten übernahmen Spaltennamen wörtlich — „93 points den 5.
final_rank", „168 erzielte_tore". In der Falken-App stehen diese Sätze seit
Build 567 als antippbare Karten und werden von Fans gelesen.

Der Ansatz: dem Modell gar keine englischen Feldnamen mehr zeigen, statt es zu
bitten, sie zu übersetzen. Was es nicht sieht, kann es nicht abschreiben.
"""
from __future__ import annotations

import pytest

from falken_kb.genai.handlers.fact_sql import fuer_synthese


def test_englische_feldnamen_werden_deutsch():
    zeilen = [{"season": "2025/26", "points": 93, "final_rank": 5,
               "wins": 27, "losses": 17, "goals_for": 208, "goals_against": 162}]
    (auf,) = fuer_synthese(zeilen)
    assert "points" not in auf and "final_rank" not in auf
    assert auf["Punkte"] == 93
    assert auf["Platz"] == 5
    assert auf["Siege"] == 27
    assert auf["Niederlagen"] == 17
    assert auf["erzielte Tore"] == 208
    assert auf["Gegentore"] == 162


def test_spielerstatistik_wird_deutsch():
    (auf,) = fuer_synthese([{"player": "Calder ANDERSON", "goals": 30,
                             "assists": 38, "points": 68, "games_played": 52}])
    assert auf["Tore"] == 30
    assert auf["Vorlagen"] == 38
    assert auf["Punkte"] == 68
    assert auf["Spiele"] == 52


def test_unterstrichene_deutsche_felder_werden_lesbar():
    """Auch selbst vergebene Aliasse wie erzielte_tore sind Feldnamen."""
    (auf,) = fuer_synthese([{"spiele": 57, "siege": 22, "niederlagen": 35,
                             "erzielte_tore": 168, "kassierte_tore": 208}])
    assert "erzielte_tore" not in auf and "kassierte_tore" not in auf
    assert auf["erzielte Tore"] == 168
    assert auf["Gegentore"] == 208
    assert auf["Spiele"] == 57


@pytest.mark.parametrize("roh,erwartet", [
    ("Calder ANDERSON", "Calder Anderson"),
    ("Aiden WAGNER", "Aiden Wagner"),
    ("Patrick BERGER", "Patrick Berger"),
    ("Nolan Ritchie", "Nolan Ritchie"),          # bereits normal
    ("Jean-Luc GRAND-PIERRE", "Jean-Luc Grand-Pierre"),
])
def test_spielernamen_in_normaler_schreibweise(roh, erwartet):
    (auf,) = fuer_synthese([{"player": roh, "points": 1}])
    assert auf["Spieler"] == erwartet


def test_vereinsnamen_bleiben_unangetastet():
    """Team-Kürzel sind keine Personennamen — ECDC darf nicht zu Ecdc werden."""
    (auf,) = fuer_synthese([{"team": "ECDC Memmingen Indians", "heim": "EV Landshut",
                             "liga": "DEL2", "punkte": 93}])
    assert auf["Team"] == "ECDC Memmingen Indians"
    assert auf["Heim"] == "EV Landshut"
    assert auf["Liga"] == "DEL2"


def test_unbekannte_felder_behalten_ihren_wert():
    """Werte bleiben unangetastet — nur die Beschriftung wird lesbar."""
    (auf,) = fuer_synthese([{"irgendwas_eigenes": 5, "points": 3}])
    assert auf["Irgendwas eigenes"] == 5
    assert auf["Punkte"] == 3


def test_leere_eingabe_bleibt_leer():
    assert fuer_synthese([]) == []


def test_nichtwoerterbuch_zeilen_stuerzen_nicht_ab():
    assert fuer_synthese(["roh", 42]) == ["roh", 42]


def test_erfundene_aliasse_verlieren_die_unterstriche():
    """Das Modell erfindet Aliasse wie gesamt_spiele — auch die dürfen nicht
    als Feldname in der Antwort landen."""
    (auf,) = fuer_synthese([{"gesamt_spiele": 57, "anzahl_siege": 22}])
    assert not any("_" in k for k in auf), auf
    assert auf["Gesamt spiele"] == 57
    assert auf["Anzahl siege"] == 22
