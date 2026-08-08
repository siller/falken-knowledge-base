"""Vertragstests der Frage-Schnittstelle (U1).

Der Vertrag ist das, woran die Convex-Vermittlung hängt (U2) — deshalb wird er
hier festgeschrieben, bevor es die Umsetzung gibt. Die Pipeline selbst ist in
allen Tests ersetzt: geprüft wird die Schnittstelle, nicht die Antwortqualität.
"""
from __future__ import annotations

import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from falken_kb.api import app as api_modul
from falken_kb.genai.web_search import suche_aktiv

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
    assert daten["quellen"] == [
        {"titel": "Falken-Bericht", "url": "https://stimme.de/x", "herkunft": None}
    ]
    assert daten["kategorie"] == "web_research"


def test_ohne_websuche_bleibt_die_antwort_bei_der_datenbank(client, monkeypatch):
    """Deckt R10: Convex unterdrückt die Websuche bei Last oder leerem Budget."""
    gesehen: dict[str, object] = {}

    def gefangen(frage, context=None):
        gesehen["aktiv"] = suche_aktiv()
        return _antwort()

    monkeypatch.setattr(api_modul, "answer", gefangen)
    r = client.post("/frage", json={"frage": "Wer war Topscorer 2024/25?", "websuche": False},
                    headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 200
    assert r.json()["websuche_genutzt"] is False
    assert gesehen["aktiv"] is False      # während des Aufrufs abgeschaltet …
    assert suche_aktiv() is True          # … danach wieder frei


def test_abschaltung_trifft_nur_die_eigene_anfrage(client, monkeypatch):
    """Der Rückfall greift unter Last — dann laufen Anfragen gleichzeitig.

    Eine Anfrage ohne Websuche darf einer parallel laufenden Anfrage die Suche
    nicht wegnehmen. Genau das passierte, solange der Schalter global war.
    """
    beobachtet: list[tuple[str, bool]] = []
    barriere = threading.Barrier(2, timeout=10)

    def gefangen(frage, context=None):
        barriere.wait()               # beide Anfragen sind jetzt gleichzeitig drin
        beobachtet.append((frage, suche_aktiv()))
        return _antwort()

    monkeypatch.setattr(api_modul, "answer", gefangen)

    def stellen(frage: str, websuche: bool):
        client.post("/frage", json={"frage": frage, "websuche": websuche},
                    headers={"X-Falken-Token": TOKEN})

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda a: stellen(*a), [("ohne", False), ("mit", True)]))

    zustand = dict(beobachtet)
    assert zustand["ohne"] is False
    assert zustand["mit"] is True


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


# ── Zeitgrenze ────────────────────────────────────────────────────────────────

def test_zu_lange_antwort_wird_zu_504(client, monkeypatch):
    """Hängt die Pipeline, bekommt der Aufrufer eine klare Absage statt zu warten.

    Geprüft wird hier nur der Statuscode. Dass die Absage auch WIRKLICH früh
    kommt, lässt sich mit dem TestClient nicht zeigen: sein Portal hält die
    Antwort zurück, bis der Arbeits-Thread fertig ist. Am echten uvicorn kam
    das 504 gemessen nach 1,03 s zurück, während die Pipeline noch 20 s
    weiterlief (08.08.2026).
    """
    monkeypatch.setattr(api_modul.settings, "api_zeitgrenze_sec", 0.2)

    def haengt(frage, context=None):
        time.sleep(1)
        return _antwort()

    monkeypatch.setattr(api_modul, "answer", haengt)
    r = client.post("/frage", json={"frage": "Egal"}, headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 504
    assert "1 Sekunden" not in r.json()["fehler"]  # Grenze, nicht Pipeline-Dauer


def test_schnelle_antwort_bleibt_unberuehrt(client, monkeypatch):
    monkeypatch.setattr(api_modul.settings, "api_zeitgrenze_sec", 5)
    monkeypatch.setattr(api_modul, "answer", lambda frage, context=None: _antwort())
    r = client.post("/frage", json={"frage": "Egal"}, headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 200


# ── Sammelaufruf für den Spieltags-Vorrat ────────────────────────────────────

def test_sammelaufruf_beantwortet_alle_fragen(client, monkeypatch):
    monkeypatch.setattr(api_modul, "answer",
                        lambda frage, context=None: _antwort(answer=f"Antwort auf {frage}"))
    r = client.post("/fragen", json={"fragen": ["Bilanz gegen Memmingen", "Letztes Duell"]},
                    headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 200
    ergebnisse = r.json()["ergebnisse"]
    assert [e["frage"] for e in ergebnisse] == ["Bilanz gegen Memmingen", "Letztes Duell"]
    assert all(e["antwort"]["beantwortet"] for e in ergebnisse)


def test_eine_kaputte_frage_kippt_den_sammelaufruf_nicht(client, monkeypatch):
    """Der Vorrat läuft nachts ohne Aufsicht — ein Ausfall darf nicht alles verwerfen."""
    def teils_kaputt(frage, context=None):
        if "kaputt" in frage:
            raise RuntimeError("DGX weg")
        return _antwort()

    monkeypatch.setattr(api_modul, "answer", teils_kaputt)
    r = client.post("/fragen", json={"fragen": ["gut", "kaputt", "auch gut"]},
                    headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 200
    ergebnisse = r.json()["ergebnisse"]
    assert ergebnisse[0]["antwort"] is not None and ergebnisse[0]["fehler"] is None
    assert ergebnisse[1]["antwort"] is None and "DGX" in ergebnisse[1]["fehler"]
    assert ergebnisse[2]["antwort"] is not None


def test_sammelaufruf_arbeitet_standardmaessig_nacheinander():
    """Gegen die DGX ist nacheinander gemessen schneller — das ist die Vorgabe."""
    from falken_kb.config import Settings

    assert Settings().api_sammel_parallel == 1


def test_parallelitaet_ist_einstellbar(client, monkeypatch):
    """Die Mechanik bleibt vorhanden, falls ein anderes Backend davon profitiert."""
    monkeypatch.setattr(api_modul.settings, "api_sammel_parallel", 5)
    monkeypatch.setattr(api_modul, "answer",
                        lambda frage, context=None: (time.sleep(0.4), _antwort())[1])
    start = time.time()
    r = client.post("/fragen", json={"fragen": [f"Frage {i}" for i in range(5)]},
                    headers={"X-Falken-Token": TOKEN})
    dauer = time.time() - start
    assert r.status_code == 200
    assert dauer < 1.4, f"{dauer:.1f}s — die Einstellung greift nicht"


def test_sammelaufruf_begrenzt_die_menge(client):
    r = client.post("/fragen", json={"fragen": [f"F{i}" for i in range(11)]},
                    headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 422


def test_sammelaufruf_braucht_das_geheimnis(client):
    r = client.post("/fragen", json={"fragen": ["Egal"]})
    assert r.status_code == 401


def test_sammelaufruf_liefert_teilergebnis_bei_gesamtgrenze(client, monkeypatch):
    """Reißt die Gesamtzeit, kommt zurück was fertig ist — nicht gar nichts."""
    monkeypatch.setattr(api_modul.settings, "api_sammel_gesamt_sec", 0.6)
    monkeypatch.setattr(api_modul.settings, "api_zeitgrenze_sec", 10)

    zaehler = {"n": 0}

    def langsamer_werdend(frage, context=None):
        zaehler["n"] += 1
        time.sleep(0.05 if zaehler["n"] == 1 else 3)
        return _antwort()

    monkeypatch.setattr(api_modul, "answer", langsamer_werdend)
    r = client.post("/fragen", json={"fragen": ["schnell", "langsam", "auch langsam"]},
                    headers={"X-Falken-Token": TOKEN})
    assert r.status_code == 200
    ergebnisse = r.json()["ergebnisse"]
    assert ergebnisse[0]["antwort"] is not None, "die fertige Frage muss geliefert werden"
    assert any(e["fehler"] and "Gesamtzeit" in e["fehler"] for e in ergebnisse[1:])
