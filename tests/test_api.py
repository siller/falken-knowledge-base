"""Vertragstests der Frage-Schnittstelle (U1).

Der Vertrag ist das, woran die Convex-Vermittlung hängt (U2) — deshalb wird er
hier festgeschrieben, bevor es die Umsetzung gibt. Die Pipeline selbst ist in
allen Tests ersetzt: geprüft wird die Schnittstelle, nicht die Antwortqualität.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from falken_kb.api import app as api_modul

TOKEN = "test-geheimnis"


@pytest.fixture(autouse=True)
def _token(monkeypatch):
    monkeypatch.setattr(api_modul.settings, "api_token", TOKEN)


@pytest.fixture
def client() -> TestClient:
    return TestClient(api_modul.app)


def _antwort(**felder):
    """Nachbau dessen, was orchestrator.answer liefert."""
    basis = {
        "answer": "Nolan Ritchie war Topscorer 2024/25 mit 84 Punkten.",
        "category": "fact",
        "sources": [],
        "web_results": [],
    }
    basis.update(felder)
    return basis


def test_frage_liefert_antwort_und_quellen(client, monkeypatch):
    monkeypatch.setattr(api_modul, "answer", lambda frage, context=None: _antwort(
        category="web_research",
        web_results=[{"title": "Falken-Bericht", "url": "https://stimme.de/x", "content": "…"}],
    ))
    r = client.post("/frage", json={"frage": "Wer war Topscorer 2024/25?"},
                    headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 200
    daten = r.json()
    assert "Ritchie" in daten["antwort"]
    assert daten["websuche_genutzt"] is True
    assert daten["quellen"] == [{"titel": "Falken-Bericht", "url": "https://stimme.de/x"}]
    assert daten["kategorie"] == "web_research"


def test_ohne_websuche_bleibt_die_antwort_bei_der_datenbank(client, monkeypatch):
    """Deckt R10: Convex unterdrückt die Websuche bei Last oder leerem Budget."""
    gesehen: dict[str, object] = {}

    def gefangen(frage, context=None):
        gesehen["provider"] = api_modul.settings.web_search_provider
        return _antwort()

    monkeypatch.setattr(api_modul, "answer", gefangen)
    r = client.post("/frage", json={"frage": "Wer war Topscorer 2024/25?", "websuche": False},
                    headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 200
    assert r.json()["websuche_genutzt"] is False
    # Während des Aufrufs war die Websuche wirklich abgeschaltet …
    assert gesehen["provider"] == "aus"
    # … und danach steht die Einstellung wieder wie vorher.
    assert api_modul.settings.web_search_provider != "aus"


def test_fehlanzeige_bleibt_status_200(client, monkeypatch):
    """Deckt R6: keine Daten ist eine Antwort, kein Fehler."""
    monkeypatch.setattr(api_modul, "answer",
                        lambda frage, context=None: _antwort(answer="keine Daten"))
    r = client.post("/frage", json={"frage": "Wie viele Zuschauer kamen 1974?"},
                    headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 200
    assert r.json()["antwort"] == "keine Daten"
    assert r.json()["beantwortet"] is False


@pytest.mark.parametrize("text", [
    "keine Daten",
    "Die bereitgestellten Quellen enthalten keine Informationen über den Besitzer.",
    "Basierend auf den vorliegenden Daten lässt sich nicht feststellen, wer gemeint ist.",
    "Zu diesem Spieler liegen keine Angaben vor.",
])
def test_fehlanzeigen_werden_erkannt(client, monkeypatch, text):
    """Wortlaute aus echten Antworten der Pipeline, nicht erfunden."""
    monkeypatch.setattr(api_modul, "answer", lambda frage, context=None: _antwort(answer=text))
    r = client.post("/frage", json={"frage": "Egal"}, headers={"X-Falken-Token": TOKEN})
    assert r.json()["beantwortet"] is False


def test_echte_antwort_gilt_als_beantwortet(client, monkeypatch):
    monkeypatch.setattr(api_modul, "answer", lambda frage, context=None: _antwort())
    r = client.post("/frage", json={"frage": "Egal"}, headers={"X-Falken-Token": TOKEN})
    assert r.json()["beantwortet"] is True


def test_falsches_geheimnis_wird_abgewiesen(client):
    r = client.post("/frage", json={"frage": "Egal"}, headers={"X-Falken-Token": "falsch"})
    assert r.status_code == 401


def test_fehlendes_geheimnis_wird_abgewiesen(client):
    r = client.post("/frage", json={"frage": "Egal"})
    assert r.status_code == 401


def test_pipeline_fehler_wird_zu_503(client, monkeypatch):
    def kracht(frage, context=None):
        raise RuntimeError("DGX nicht erreichbar")

    monkeypatch.setattr(api_modul, "answer", kracht)
    r = client.post("/frage", json={"frage": "Egal"}, headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 503
    assert "DGX" in r.json()["fehler"]


def test_leere_frage_wird_abgewiesen(client):
    r = client.post("/frage", json={"frage": "   "}, headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 422


def test_zustandspruefung_braucht_kein_geheimnis(client):
    r = client.get("/gesundheit")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
