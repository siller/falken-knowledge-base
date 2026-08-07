"""Web-Search für die KB — Exa als Primär-Anbieter, Tavily als Fallback.

Auswahl gemessen statt geraten (25.07.2026, sechs Standard-Queries à 8 Treffer,
gezählt wurden Treffer auf den Domains aus `web_news.ALLOWED_DOMAINS`):

    Exa                 40/48   ~1,1 s pro Suche
    Tavily allgemein    22/48   ~2,4 s
    Tavily topic=news    3/48   ~2,7 s

Exa kostet ~$0,007 pro Suche, Tavily ist im Free-Tier gratis (1.000/Monat) —
deshalb Exa zuerst, Tavily automatisch als Rückfall, wenn Exa fehlt oder kippt.
Beide Anbieter liefern dasselbe normalisierte Format zurück.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator

import httpx

from ..config import settings

logger = logging.getLogger(__name__)


def _normalized(answer: str, results: list[dict[str, Any]], provider: str) -> dict[str, Any]:
    return {"answer": answer, "results": results, "error": None, "provider": provider}


def exa_search(
    query: str,
    max_results: int = 5,
    max_chars: int = 800,
) -> dict[str, Any]:
    """Web-Search via Exa. Liefert Volltext-Auszüge statt nur Snippets."""
    api_key = settings.exa_api_key
    if not api_key:
        return {"error": "EXA_API_KEY nicht gesetzt", "results": [], "answer": ""}

    try:
        with httpx.Client(timeout=30) as c:
            r = c.post(
                "https://api.exa.ai/search",
                headers={"x-api-key": api_key, "Content-Type": "application/json"},
                json={
                    "query": query,
                    "numResults": max_results,
                    "contents": {"text": {"maxCharacters": max_chars}},
                },
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        code = e.response.status_code
        grund = {
            401: "Exa-Key wird abgelehnt (401) — Key in den Secrets prüfen",
            403: "Exa-Zugriff verweigert (403)",
            429: "Exa-Kontingent erschöpft (429)",
        }.get(code, f"Exa HTTP {code}")
        logger.warning("Exa-Fehler: %s", grund)
        return {"error": grund, "results": [], "answer": ""}
    except httpx.HTTPError as e:
        logger.warning("Exa-Fehler: %s", str(e)[:200])
        return {"error": str(e)[:200], "results": [], "answer": ""}

    return _normalized(
        # Exa liefert keine fertige Antwort — die Synthese macht ohnehin der LLM.
        "",
        [
            {
                "title": x.get("title") or "",
                "url": x.get("url") or "",
                "content": (x.get("text") or "")[:max_chars],
                "published": x.get("publishedDate") or None,
            }
            for x in (data.get("results") or [])
        ],
        "exa",
    )


# Werte, mit denen die Websuche dauerhaft stillgelegt wird (Konfiguration).
_AUS = ("aus", "off", "none", "deaktiviert")

# Abschaltung für EINEN Aufruf. Bewusst ein ContextVar und keine Änderung an
# `settings`: der Frage-Dienst bedient mehrere Anfragen gleichzeitig, und eine
# globale Umschaltung würde einer parallel laufenden Anfrage die Websuche
# wegnehmen — ausgerechnet unter Last, wo der Rückfall überhaupt erst greift.
_unterdrueckt: ContextVar[bool] = ContextVar("websuche_unterdrueckt", default=False)


@contextmanager
def websuche_aus() -> Iterator[None]:
    """Schaltet die Websuche nur für den laufenden Aufruf ab."""
    marke = _unterdrueckt.set(True)
    try:
        yield
    finally:
        _unterdrueckt.reset(marke)


def suche_aktiv() -> bool:
    """Ist die Websuche für den laufenden Aufruf zugelassen?"""
    if _unterdrueckt.get():
        return False
    if (settings.web_search_provider or "auto").lower() in _AUS:
        return False
    return bool(settings.exa_api_key or settings.tavily_api_key)


def web_search(query: str, max_results: int = 5, max_chars: int = 800) -> dict[str, Any]:
    """Sucht beim konfigurierten Anbieter, mit automatischem Rückfall.

    `WEB_SEARCH_PROVIDER=exa|tavily|auto` (Default auto: Exa wenn Key vorhanden).
    Liefert Exa keine Treffer oder fehlt der Key, übernimmt Tavily — eine
    Websuche soll nicht daran scheitern, dass ein Anbieter zickt.
    """
    provider = (settings.web_search_provider or "auto").lower()
    if _unterdrueckt.get() or provider in _AUS:
        return {"error": "Websuche ist abgeschaltet", "results": [], "answer": "",
                "provider": "aus"}
    use_exa = provider == "exa" or (provider == "auto" and bool(settings.exa_api_key))

    if use_exa:
        res = exa_search(query, max_results=max_results, max_chars=max_chars)
        if res.get("results"):
            return res
        logger.info("Exa lieferte nichts (%s) — Fallback auf Tavily", res.get("error") or "0 Treffer")
        if provider == "exa":
            return res  # explizit auf Exa festgelegt: kein stiller Anbieterwechsel

    res = tavily_search(query, max_results=max_results)
    res.setdefault("provider", "tavily")
    return res


def tavily_search(
    query: str,
    max_results: int = 5,
    include_answer: bool = True,
    search_depth: str = "basic",
) -> dict[str, Any]:
    """Web-Search via Tavily.

    Returnt dict mit:
      - 'answer' (kurze AI-Summary, kann leer sein)
      - 'results' [{'title','url','content'}, ...]
      - 'error' (nur wenn fehlgeschlagen)
    """
    api_key = settings.tavily_api_key
    if not api_key:
        return {"error": "TAVILY_API_KEY nicht gesetzt", "results": [], "answer": ""}
    if api_key.strip().upper().startswith("REPLACE_ME"):
        return {"error": "TAVILY_API_KEY ist noch der Platzhalter aus der Vorlage",
                "results": [], "answer": ""}

    try:
        with httpx.Client(timeout=20) as c:
            r = c.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": api_key,
                    "query": query,
                    "search_depth": search_depth,
                    "include_answer": include_answer,
                    "max_results": max_results,
                },
            )
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPStatusError as e:
        # Konkreter Grund statt "irgendwas ging schief" — sonst ist von außen
        # nicht zu unterscheiden, ob der Key fehlt, abgelehnt wird oder das
        # Monatskontingent aufgebraucht ist.
        code = e.response.status_code
        grund = {
            401: "API-Key wird abgelehnt (401) — Key in den Secrets prüfen",
            403: "Zugriff verweigert (403) — Key ungültig oder gesperrt",
            429: "Kontingent erschöpft (429) — Tavily-Limit erreicht",
        }.get(code, f"HTTP {code}")
        logger.warning("Tavily-Fehler: %s", grund)
        return {"error": grund, "results": [], "answer": ""}
    except httpx.HTTPError as e:
        logger.warning("Tavily-Fehler: %s", str(e)[:200])
        return {"error": str(e)[:200], "results": [], "answer": ""}

    return {
        "answer": data.get("answer") or "",
        "results": [
            {
                "title": x.get("title", ""),
                "url": x.get("url", ""),
                "content": x.get("content", "")[:500],
            }
            for x in (data.get("results") or [])
        ],
        "error": None,
    }
