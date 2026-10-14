"""„letzte Saison“ ist die letzte ABGESCHLOSSENE, nicht die laufende.

WHY: Solange 2026/27 ohne Ergebnisse in der DB stand, lösten „aktuelle“ und
„letzte Saison“ beide über max(season) mit gespielten Spielen auf 2025/26 auf —
zufällig richtig. Seit die laufende Saison Ergebnisse hat, nannte HORST auf
„Wer war in der letzten Saison der beste Scorer?“ den Topscorer von 2026/27.
Die Prompt-Regel allein hielt das Modell nicht ab, deshalb ersetzt der Code den
Ausdruck, sobald die Frage die Vorsaison meint.
"""
from __future__ import annotations

import pytest

from falken_kb.genai.handlers.fact_sql import (
    LETZTE_ABGESCHLOSSENE_SAISON,
    SCHEMA_CONTEXT,
    _letzte_saison_einsetzen,
)

_GENERIERT = (
    "SELECT player, points FROM falken_skater_stats WHERE season = "
    "(SELECT max(season) FROM season_standings WHERE team = 'Heilbronner Falken' AND games_played > 0) "
    "AND points IS NOT NULL ORDER BY points DESC NULLS LAST LIMIT 1;"
)


@pytest.mark.parametrize("frage", [
    "Wer war in der letzten Saison der beste Scorer der Falken?",
    "Wie lief die letzte Saison für die Falken?",
    "Wer war Topscorer der vergangenen Saison?",
    "Wie viele Punkte hatten die Falken in der vorigen Saison?",
    "Wer war in der Vorsaison bester Torschütze?",
])
def test_vorsaison_wird_auf_letzte_abgeschlossene_saison_umgestellt(frage):
    neu = _letzte_saison_einsetzen(frage, _GENERIERT)
    assert neu is not None
    assert LETZTE_ABGESCHLOSSENE_SAISON in neu
    assert "games_played > 0" not in neu


@pytest.mark.parametrize("frage", [
    "Wer ist der aktuelle Topscorer der Falken in dieser Saison?",
    "Wer war bester Scorer der letzten 5 Saisons?",
    "Wie war die Bilanz in den letzten Saisons?",
])
def test_aktuelle_saison_und_mehrere_saisons_bleiben_unberuehrt(frage):
    assert _letzte_saison_einsetzen(frage, _GENERIERT) is None


def test_cte_alias_bleibt_erhalten():
    sql = ("WITH vorher AS (SELECT max(season) AS label FROM season_standings "
           "WHERE team = 'Heilbronner Falken' AND games_played > 0) SELECT label FROM vorher")
    neu = _letzte_saison_einsetzen("Wer kam in der letzten Saison dazu?", sql)
    assert neu is not None and "AS label" in neu and "SELECT label FROM vorher" in neu


def test_neuzugaenge_beispiel_vergleicht_mit_der_abgeschlossenen_saison():
    """Sonst vergleicht es den laufenden Kader mit sich selbst — 0 Neuzugänge."""
    beispiel = SCHEMA_CONTEXT.split('-- Dasselbe ohne genannte Saison ("neu im Kader"')[1].split("ORDER BY f.player;")[0]
    assert "games_played > 0" not in beispiel
    assert "g.home_score IS NULL AND g.date > now()" in beispiel


def test_neueste_saison_per_sortierung_wird_ebenfalls_eingeschraenkt():
    """Zweite Form, die das Modell für "letzte Saison" erzeugt."""
    sql = ("SELECT season, final_rank, points FROM season_standings WHERE team = 'Heilbronner Falken' "
           "AND games_played > 0 ORDER BY season DESC LIMIT 1;")
    neu = _letzte_saison_einsetzen("Wie lief die letzte Saison für die Falken?", sql)
    assert neu is not None
    assert f"FROM season_standings WHERE season <= {LETZTE_ABGESCHLOSSENE_SAISON} AND team" in neu


def test_sortierung_ohne_limit_1_bleibt_unberuehrt():
    sql = "SELECT season, points FROM season_standings WHERE team = 'Heilbronner Falken' ORDER BY season DESC;"
    assert _letzte_saison_einsetzen("Wie lief die letzte Saison?", sql) is None
