"""Screenshot der Streamlit-App in gewünschter Bildschirmbreite.

WHY: Mobile-Layout lässt sich nicht erraten. Headless-Chrome liefert ein Bild,
das man ansehen kann — Vorher/Nachher statt Vermutung.

    python3 scripts/ui_screenshot.py --width 390 --height 844 --out /tmp/mobil.png
"""
from __future__ import annotations

import argparse
import os
import signal
import shutil
import socket
import subprocess
import tempfile
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def _freier_port() -> int:
    with socket.socket() as s:
        s.bind(("", 0))
        return s.getsockname()[1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--width", type=int, default=390)
    ap.add_argument("--height", type=int, default=844)
    ap.add_argument("--out", required=True)
    ap.add_argument("--wartezeit", type=int, default=20000, help="ms für JS-Rendering")
    ap.add_argument("--startzeit", type=int, default=20, help="Sekunden Vorlauf für den App-Start")
    args = ap.parse_args()

    if not Path(CHROME).exists():
        print(f"Chrome nicht gefunden unter {CHROME} — Pfad im Skript anpassen.",
              file=sys.stderr)
        return 1

    port = _freier_port()
    umgebung = dict(os.environ)
    umgebung.pop("APP_PASSWORD", None)

    # Streamlit liest .streamlit/ aus dem Arbeitsverzeichnis. Wir bauen eine
    # Kopie OHNE app_password — sonst zeigt der Screenshot nur den Login-Schirm.
    # Alles andere (Theme, DB-Keys) bleibt gleich; die App-Pfade sind absolut.
    arbeitsdir = tempfile.mkdtemp(prefix="falken-shot-")
    ziel = Path(arbeitsdir) / ".streamlit"
    ziel.mkdir()
    quelle = ROOT / ".streamlit"
    if (quelle / "config.toml").exists():
        shutil.copy(quelle / "config.toml", ziel / "config.toml")
    if (quelle / "secrets.toml").exists():
        gefiltert = [z for z in (quelle / "secrets.toml").read_text().splitlines()
                     if not z.strip().startswith("app_password")]
        (ziel / "secrets.toml").write_text("\n".join(gefiltert) + "\n")

    app = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "frontend" / "falken_ui.py"),
         "--server.port", str(port), "--server.headless", "true"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=umgebung,
        cwd=arbeitsdir, preexec_fn=os.setsid,
    )
    def chrome(ziel_datei: str, budget: int) -> None:
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", f"--screenshot={ziel_datei}",
             f"--window-size={args.width},{args.height}",
             f"--virtual-time-budget={budget}", f"http://localhost:{port}/"],
            capture_output=True, timeout=180,
        )

    try:
        time.sleep(args.startzeit)  # Streamlit-Start + erste Verbindung zur DB
        # Erster Durchlauf nur zum Aufwärmen: Streamlit führt das Skript beim
        # ersten Websocket-Kontakt aus (Secrets, Settings, DB-Client). Ohne das
        # zeigt der Screenshot nur Streamlits "RUNNING…"-Skelett.
        chrome(str(Path(arbeitsdir) / "warmup.png"), 15000)
        chrome(args.out, args.wartezeit)
    finally:
        os.killpg(os.getpgid(app.pid), signal.SIGTERM)
        shutil.rmtree(arbeitsdir, ignore_errors=True)

    if Path(args.out).exists():
        print(f"Screenshot: {args.out} ({Path(args.out).stat().st_size} Bytes)")
        return 0
    print("Kein Screenshot entstanden", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
