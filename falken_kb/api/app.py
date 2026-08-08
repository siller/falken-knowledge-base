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

import asyncio
import logging
import time
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse

from ..config import settings
from ..genai.orchestrator import answer
from ..genai.web_search import websuche_aus
from ..logging_setup import setup_logging
from .modelle import (
    FrageAnfrage,
    FrageAntwort,
    Quelle,
    SammelAnfrage,
    SammelAntwort,
    SammelErgebnis,
)

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


def _quellen(ergebnis: dict[str, Any]) -> list[Quelle]:
    """Quellen aus den unterschiedlichen Handler-Formen einsammeln."""
    quellen: list[Quelle] = []
    for treffer in ergebnis.get("web_results") or []:
        if treffer.get("url"):
            quellen.append(Quelle(titel=treffer.get("title") or treffer["url"],
                                  url=treffer["url"]))
    for artikel in ergebnis.get("sources") or []:
        # RAG-Quellen tragen Titel und Herkunft, aber nicht immer eine URL.
        # `url` bleibt dann leer statt die Domain vorzutäuschen — die App darf
        # nichts anzubieten haben, das beim Antippen ins Leere führt.
        quellen.append(Quelle(titel=artikel.get("title") or "Artikel",
                              herkunft=artikel.get("source") or None,
                              url=artikel.get("url") or None))
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


def _beantworte(frage: str, kontext: str | None, websuche: bool) -> FrageAntwort:
    """Eine Frage durch die Pipeline schicken und in die Antwortform bringen."""
    start = time.time()
    if websuche:
        ergebnis = answer(frage, context=kontext)
    else:
        with websuche_aus():
            ergebnis = answer(frage, context=kontext)

    text = str(ergebnis.get("answer") or "").strip()
    return FrageAntwort(
        antwort=text,
        quellen=_quellen(ergebnis),
        kategorie=str(ergebnis.get("category") or "unbekannt"),
        websuche_genutzt=bool(websuche),
        beantwortet=bool(text) and not any(m in text.lower() for m in _FEHLANZEIGE),
        dauer_ms=int((time.time() - start) * 1000),
    )


async def _mit_zeitgrenze(fn, *args) -> Any:
    """Führt die synchrone Pipeline aus und bricht nach der Zeitgrenze ab.

    WICHTIG: Der Thread läuft danach weiter — Python kann ihn nicht abbrechen.
    Der Aufrufer ist aber frei, und darum geht es: ohne diese Grenze hängt der
    Convex-Aufruf, bis dessen eigenes Zeitlimit greift. Dass der Faden noch
    zappelt, ist mit der Zeitgrenze im Modell-Client (30s) und deren Retries
    zeitlich gedeckelt.
    """
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(fn, *args), timeout=settings.api_zeitgrenze_sec
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Keine Antwort binnen {settings.api_zeitgrenze_sec:.0f} Sekunden",
        ) from None


@app.post("/frage", response_model=FrageAntwort, responses={401: {}, 503: {}, 504: {}})
async def frage_stellen(
    anfrage: FrageAnfrage,
    x_falken_token: str | None = Header(default=None, alias="X-Falken-Token"),
) -> FrageAntwort:
    _pruefe_token(x_falken_token)
    try:
        return await _mit_zeitgrenze(
            _beantworte, anfrage.frage, anfrage.kontext, anfrage.websuche
        )
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001 — jeder Ausfall wird zu 503, nie zu einem Absturz
        logger.exception("Frage fehlgeschlagen: %s", anfrage.frage[:80])
        raise HTTPException(status_code=503, detail=str(e)[:200]) from e


@app.post("/fragen", response_model=SammelAntwort, responses={401: {}, 422: {}})
async def fragen_stellen(
    anfrage: SammelAnfrage,
    x_falken_token: str | None = Header(default=None, alias="X-Falken-Token"),
) -> SammelAntwort:
    """Mehrere Fragen in einem Aufruf — für den nächtlichen Spieltags-Vorrat.

    Der Gewinn ist NICHT Geschwindigkeit: gemessen ist Nacheinander sogar
    schneller als parallel (siehe `api_sammel_parallel` in der Config). Der
    Gewinn ist eine Verbindung statt fünf, ein Aufruf für Convex — und dass
    eine gescheiterte Frage die anderen nicht mitnimmt.
    """
    _pruefe_token(x_falken_token)
    start = time.time()

    async def eine(frage: str) -> SammelErgebnis:
        try:
            antwort = await _mit_zeitgrenze(_beantworte, frage, None, anfrage.websuche)
            return SammelErgebnis(frage=frage, antwort=antwort)
        except HTTPException as e:
            return SammelErgebnis(frage=frage, fehler=str(e.detail)[:200])
        except Exception as e:  # noqa: BLE001
            logger.warning("Frage im Sammelaufruf gescheitert (%s): %s", frage[:50], e)
            return SammelErgebnis(frage=frage, fehler=str(e)[:200])

    bremse = asyncio.Semaphore(settings.api_sammel_parallel)

    async def gebremst(frage: str) -> SammelErgebnis:
        async with bremse:
            return await eine(frage)

    ergebnisse = await asyncio.gather(*(gebremst(f) for f in anfrage.fragen))
    return SammelAntwort(ergebnisse=list(ergebnisse),
                         dauer_ms=int((time.time() - start) * 1000))


@app.exception_handler(HTTPException)
def _fehler_als_json(_request, exc: HTTPException) -> JSONResponse:
    """Einheitliches Fehlerformat: immer {"fehler": ...}."""
    return JSONResponse(status_code=exc.status_code, content={"fehler": str(exc.detail)})
