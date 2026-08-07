"""HTTP-Schnittstelle vor HORST (U1).

WHY: HORST war bisher nur über die Streamlit-Oberfläche erreichbar. Die
Falken-App fragt über einen Convex-Dienst, und der braucht HTTP. Die
Schnittstelle ist bewusst dünn — sie übersetzt, sie entscheidet nicht: Deckel,
Live-Erkennung und Rückfall liegen in Convex, weil nur dort alle laufenden
Fragen sichtbar sind.

Start:
    uvicorn falken_kb.api.app:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

import logging
import time
from contextlib import contextmanager
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from ..config import settings
from ..genai.orchestrator import answer
from ..logging_setup import setup_logging
from .modelle import FrageAnfrage, FrageAntwort, Quelle

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HORST-Frage-Schnittstelle",
    version="1.0",
    description="Fragen zu den Heilbronner Falken, beantwortet aus Vereinsdaten, "
                "News und Websuche.",
)

# Wortlaute, mit denen die Pipeline eine Fehlanzeige meldet. Sie sind eine
# gültige Antwort, kein Fehler — die App zeigt sie an, statt einen Fehlerzustand.
# Die Liste stammt aus beobachteten Antworten, nicht aus Vermutung; sie bleibt
# eine Heuristik. Im Zweifel gilt eine Antwort als beantwortet, weil `beantwortet`
# nur Darstellung und Auswertung steuert, nie ob der Text angezeigt wird.
_FEHLANZEIGE = (
    "keine daten",
    "nicht verfügbar",
    "konnte für diese frage kein sql",
    "keine informationen",
    "keine angaben",
    "lässt sich nicht feststellen",
    "liegen keine",
    "enthalten keine",
    "nichts belegtes",
)


@contextmanager
def _websuche_aus():
    """Schaltet die Websuche für die Dauer eines Aufrufs ab und stellt sie zurück."""
    vorher = settings.web_search_provider
    settings.web_search_provider = "aus"
    try:
        yield
    finally:
        settings.web_search_provider = vorher


def _quellen(ergebnis: dict[str, Any]) -> list[Quelle]:
    """Quellen aus den unterschiedlichen Handler-Formen einsammeln."""
    quellen: list[Quelle] = []
    for treffer in ergebnis.get("web_results") or []:
        if treffer.get("url"):
            quellen.append(Quelle(titel=treffer.get("title") or treffer["url"],
                                  url=treffer["url"]))
    for artikel in ergebnis.get("sources") or []:
        # RAG-Quellen tragen Titel und Herkunft, aber nicht immer eine URL.
        quellen.append(Quelle(titel=artikel.get("title") or "Artikel",
                              url=artikel.get("url") or artikel.get("source") or ""))
    return quellen


def _pruefe_token(token: str | None) -> None:
    if not settings.api_token:
        # Ohne gesetztes Geheimnis nimmt die Schnittstelle nichts an — sonst
        # stünde sie beim ersten Fehlstart offen im Netz.
        raise HTTPException(status_code=401, detail="Schnittstelle nicht konfiguriert")
    if token != settings.api_token:
        raise HTTPException(status_code=401, detail="Ungültiges Geheimnis")


@app.get("/gesundheit")
def gesundheit() -> dict[str, str]:
    """Zustandsprüfung für Betrieb und Deployment — ohne Geheimnis erreichbar."""
    return {"status": "ok", "modell": settings.dgx_chat_model}


@app.post("/frage", response_model=FrageAntwort, responses={401: {}, 503: {}})
def frage_stellen(
    anfrage: FrageAnfrage,
    x_falken_token: str | None = Header(default=None, alias="X-Falken-Token"),
) -> FrageAntwort:
    _pruefe_token(x_falken_token)

    start = time.time()
    try:
        if anfrage.websuche:
            ergebnis = answer(anfrage.frage, context=anfrage.kontext)
        else:
            with _websuche_aus():
                ergebnis = answer(anfrage.frage, context=anfrage.kontext)
    except Exception as e:  # noqa: BLE001 — jeder Ausfall wird zu 503, nie zu einem Absturz
        logger.exception("Frage fehlgeschlagen: %s", anfrage.frage[:80])
        raise HTTPException(status_code=503, detail=str(e)[:200]) from e

    text = str(ergebnis.get("answer") or "").strip()
    beantwortet = bool(text) and not any(m in text.lower() for m in _FEHLANZEIGE)

    return FrageAntwort(
        antwort=text,
        quellen=_quellen(ergebnis),
        kategorie=str(ergebnis.get("category") or "unbekannt"),
        websuche_genutzt=bool(anfrage.websuche),
        beantwortet=beantwortet,
        dauer_ms=int((time.time() - start) * 1000),
    )


@app.exception_handler(HTTPException)
def _fehler_als_json(_request, exc: HTTPException) -> JSONResponse:
    """Einheitliches Fehlerformat: immer {"fehler": ...}."""
    return JSONResponse(status_code=exc.status_code, content={"fehler": str(exc.detail)})
