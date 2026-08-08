"""Vertrag der Frage-Schnittstelle — Anfrage und Antwort.

Diese Formen sind das, woran die Convex-Vermittlung hängt. Änderungen hier
brechen die App, deshalb stehen sie an einer Stelle und nicht verstreut.
"""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class FrageAnfrage(BaseModel):
    frage: str = Field(min_length=1, max_length=500)
    kontext: str | None = Field(
        default=None,
        max_length=2000,
        description="Vorheriger Dialog für Folgefragen. Geht an die Handler, "
                    "nicht in die Routing-Entscheidung.",
    )
    websuche: bool = Field(
        default=True,
        description="False schaltet die Websuche für diese Frage ab — gesetzt "
                    "vom Aufrufer bei Last oder erschöpftem Tagesbudget.",
    )

    @field_validator("frage")
    @classmethod
    def _nicht_nur_leerzeichen(cls, wert: str) -> str:
        if not wert.strip():
            raise ValueError("frage darf nicht leer sein")
        return wert.strip()


class Quelle(BaseModel):
    titel: str
    # Leer, wenn die Quelle aus dem eigenen Artikelbestand kommt und keine
    # verlinkbare Adresse trägt. Die App zeigt dann Titel und Herkunft ohne Link.
    url: str | None = None
    herkunft: str | None = None


class FrageAntwort(BaseModel):
    antwort: str
    quellen: list[Quelle] = []
    kategorie: str
    websuche_genutzt: bool
    beantwortet: bool = Field(
        description="False, wenn die Pipeline keine Grundlage gefunden hat. Der "
                    "Aufruf war trotzdem erfolgreich — die Oberfläche zeigt die "
                    "Fehlanzeige als Antwort, nicht als Fehler.",
    )
    dauer_ms: int


class SammelAnfrage(BaseModel):
    """Mehrere Fragen in einem Aufruf — für den nächtlichen Spieltags-Vorrat.

    Einzeln gestellt wären das ebenso viele Verbindungen und Wartezeiten; hier
    laufen sie gebündelt und parallel.
    """

    fragen: list[str] = Field(min_length=1)
    websuche: bool = True

    @field_validator("fragen")
    @classmethod
    def _sinnvolle_menge(cls, werte: list[str]) -> list[str]:
        from ..config import settings

        sauber = [w.strip() for w in werte if w.strip()]
        if not sauber:
            raise ValueError("keine verwertbare Frage enthalten")
        if len(sauber) > settings.api_sammel_max:
            raise ValueError(f"höchstens {settings.api_sammel_max} Fragen je Aufruf")
        return sauber


class SammelErgebnis(BaseModel):
    frage: str
    antwort: FrageAntwort | None = None
    fehler: str | None = Field(
        default=None,
        description="Gesetzt, wenn genau diese Frage scheiterte. Die übrigen "
                    "Ergebnisse bleiben gültig — der Vorrat läuft nachts ohne "
                    "Aufsicht, ein Ausfall darf nicht alles verwerfen.",
    )


class SammelAntwort(BaseModel):
    ergebnisse: list[SammelErgebnis]
    dauer_ms: int


class Fehler(BaseModel):
    fehler: str
