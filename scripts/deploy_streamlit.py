"""Push auslösen und warten, bis Streamlit Cloud den neuen Stand wirklich ausliefert.

WHY: Streamlit Community Cloud baut zwar bei jedem Push neu, aber ohne Rückmeldung —
zweimal wurde deshalb an einem Fehler weitergesucht, der längst behoben war, die
App aber noch alten Code lief. Ein "Reboot"-Knopf ist von außen nicht erreichbar
(keine öffentliche API), messbar ist der Zustand trotzdem:

`frontend/static/version.txt` wird unter `/app/static/version.txt` OHNE
Passwortschutz ausgeliefert. Das Skript schreibt dort einen Zeitstempel, committet,
pusht — und pollt die Live-URL, bis genau dieser Stempel ankommt.

    python3 scripts/deploy_streamlit.py                 # stempeln, pushen, warten
    python3 scripts/deploy_streamlit.py --check-only    # nur nachsehen, was live ist

Kommt der Stempel nicht an, hilft nur der Reboot-Knopf im Cloud-Dashboard —
das ist der eine Schritt, der zwingend im Browser passieren muss.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
VERSION_FILE = ROOT / "frontend" / "static" / "version.txt"
APP_URL = "https://falkenapp.streamlit.app"
# Community Cloud liefert statische Dateien NUR unter dem Präfix "/~/+" aus
# (streamlit/streamlit#12821). Ohne das Präfix bekommt man 200 plus die
# App-Shell zurück — was wie ein veralteter Deploy aussieht und mich einmal
# zu der falschen Diagnose "die App zieht den Code nicht" verleitet hat.
# Lokal gilt der Pfad ohne Präfix, deshalb werden beide probiert.
VERSION_PFADE = ("/~/+/app/static/version.txt", "/app/static/version.txt")


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=False
    ).stdout.strip()


STAMP_RE = __import__("re").compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z \w+$")


def live_version() -> str | None:
    """Liest den Stempel der laufenden App.

    WICHTIG: Die Streamlit-Edge schickt JEDEN Pfad ohne Session-Cookie auf die
    Auth-Weiterleitung — auch statische Dateien. Ohne Cookie-Handshake bekommt
    man deshalb die Login-Seite statt version.txt und hält einen erfolgreichen
    Deploy für gescheitert.
    """
    try:
        with httpx.Client(timeout=25, follow_redirects=True,
                          headers={"User-Agent": "falken-kb-deploycheck/1.0"}) as c:
            c.get(APP_URL)          # Handshake: setzt die Session-Cookies
            for pfad in VERSION_PFADE:
                r = c.get(APP_URL + pfad)
                text = (r.text or "").strip()
                if r.status_code == 200 and STAMP_RE.match(text):
                    return text
    except httpx.HTTPError:
        pass
    return None


def stamp() -> str:
    """Neuen Stempel schreiben: Zeit + aktueller Commit."""
    jetzt = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sha = _git("rev-parse", "--short", "HEAD") or "unbekannt"
    wert = f"{jetzt} {sha}"
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    VERSION_FILE.write_text(wert + "\n")
    return wert


def warte_auf_deploy(erwartet: str, minuten: int = 8) -> bool:
    ende = time.time() + minuten * 60
    zuletzt = None
    while time.time() < ende:
        aktuell = live_version()
        if aktuell == erwartet:
            return True
        if aktuell != zuletzt:
            print(f"   live: {aktuell or '(nicht erreichbar)'} — warte auf {erwartet}")
            zuletzt = aktuell
        time.sleep(15)
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check-only", action="store_true", help="nur den Live-Stand zeigen")
    ap.add_argument("--minutes", type=int, default=8, help="wie lange auf den Build warten")
    args = ap.parse_args()

    if args.check_only:
        print(f"Live: {live_version() or '(version.txt nicht erreichbar)'}")
        print(f"Lokal: {VERSION_FILE.read_text().strip() if VERSION_FILE.exists() else '(keine)'}")
        return 0

    wert = stamp()
    print(f"Stempel: {wert}")
    _git("add", str(VERSION_FILE))
    subprocess.run(["git", "-C", str(ROOT), "commit", "-q", "-m",
                    f"chore: deploy-stempel {wert}"], check=False)
    push = subprocess.run(["git", "-C", str(ROOT), "push", "-q", "origin", "main"],
                          capture_output=True, text=True)
    if push.returncode != 0:
        print("Push fehlgeschlagen:", push.stderr.strip()[:200])
        return 1
    print("Gepusht — warte auf den Rebuild …")

    if warte_auf_deploy(wert, minuten=args.minutes):
        print(f"✓ Live-Stand entspricht jetzt {wert}")
        return 0
    print(
        f"✗ Nach {args.minutes} Minuten liefert die App noch nicht den neuen Stand.\n"
        f"  Bitte einmal im Dashboard rebooten: {APP_URL} → Manage app → Reboot app.\n"
        f"  (Diesen Schritt kann nur ein eingeloggter Browser auslösen.)"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
