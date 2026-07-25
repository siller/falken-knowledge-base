# Mobile Beispielfragen-Leiste — Umsetzungsplan

> **Für agentische Bearbeiter:** ERFORDERLICHE SUB-SKILL: `superpowers:subagent-driven-development`
> (empfohlen) oder `superpowers:executing-plans`, um diesen Plan Aufgabe für Aufgabe
> abzuarbeiten. Die Schritte nutzen Checkbox-Syntax (`- [ ]`) zur Nachverfolgung.

**Ziel:** Auf dem Handy startet die App im Chat, und die Beispielfragen sind über
einen Button direkt am Eingabefeld erreichbar.

**Architektur:** Eine Aktionszeile unmittelbar vor `st.chat_input` enthält ein
`st.popover` mit den Beispielfragen und daneben den Verlauf-Button. Die Sidebar
startet über `initial_sidebar_state="auto"` auf kleinen Geräten eingeklappt und
behält Backend-Kasten und Diagnose. Alles in einer Datei, ein Codepfad für Handy
und Desktop.

**Tech-Stack:** Streamlit 1.37, reines Python, ergänzendes CSS über
`st.markdown(..., unsafe_allow_html=True)`; Abnahme per Headless-Chrome-Screenshot.

## Globale Vorgaben

- Streamlit **1.37** — `st.pills` und `st.segmented_control` gibt es dort NICHT,
  nur `st.popover`, `st.columns`, `st.button`.
- Oberflächentexte auf **Deutsch**, Ton wie bisher (z.B. „💡 Beispielfragen").
- Tippflächen **mindestens 44 px** hoch.
- Farben aus dem bestehenden Falken-Design: Rot `#c8102e`, Navy `#0a2240`.
- Die Datei `frontend/falken_ui.py` ist die einzige Datei der Oberfläche —
  keine neue UI-Datei anlegen, bestehende Struktur beibehalten.
- Kein CSS gegen undokumentierte Streamlit-Interna außer den bereits im Projekt
  genutzten `data-testid`-Selektoren.
- Nach jeder Aufgabe committen.

---

### Aufgabe 1: Screenshot-Werkzeug + Sidebar-Start

**Dateien:**
- Anlegen: `scripts/ui_screenshot.py`
- Ändern: `frontend/falken_ui.py:24` (`initial_sidebar_state`)

**Schnittstellen:**
- Erzeugt: `scripts/ui_screenshot.py --width N --height N --out PFAD` startet die
  App auf einem freien Port, schießt einen Screenshot und beendet sie wieder.
  Wird in Aufgabe 4 erneut benutzt.

- [ ] **Schritt 1: Screenshot-Werkzeug anlegen**

```python
"""Screenshot der Streamlit-App in gewünschter Bildschirmbreite.

WHY: Mobile-Layout lässt sich nicht erraten. Headless-Chrome liefert ein Bild,
das man ansehen kann — Vorher/Nachher statt Vermutung.

    python3 scripts/ui_screenshot.py --width 390 --height 844 --out /tmp/mobil.png
"""
from __future__ import annotations

import argparse
import os
import signal
import socket
import subprocess
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
    ap.add_argument("--wartezeit", type=int, default=9000, help="ms für JS-Rendering")
    args = ap.parse_args()

    port = _freier_port()
    umgebung = dict(os.environ)
    # Ohne Passwort rendert die App direkt den Chat — sonst sieht man nur den Login.
    umgebung.pop("APP_PASSWORD", None)
    app = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "frontend" / "falken_ui.py"),
         "--server.port", str(port), "--server.headless", "true"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=umgebung,
        preexec_fn=os.setsid,
    )
    try:
        time.sleep(15)  # Streamlit-Start + erste Verbindung zur DB
        subprocess.run(
            [CHROME, "--headless", "--disable-gpu", f"--screenshot={args.out}",
             f"--window-size={args.width},{args.height}",
             f"--virtual-time-budget={args.wartezeit}", f"http://localhost:{port}/"],
            capture_output=True, timeout=120,
        )
    finally:
        os.killpg(os.getpgid(app.pid), signal.SIGTERM)

    if Path(args.out).exists():
        print(f"Screenshot: {args.out} ({Path(args.out).stat().st_size} Bytes)")
        return 0
    print("Kein Screenshot entstanden", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Schritt 2: Ausgangszustand festhalten**

Run: `python3 scripts/ui_screenshot.py --width 390 --height 844 --out /tmp/mobil_vorher.png`
Erwartet: Datei entsteht; im Bild verdeckt die Sidebar den Chat vollständig.
Das Bild ansehen (Read-Tool) und den Befund notieren.

- [ ] **Schritt 3: Sidebar-Start umstellen**

In `frontend/falken_ui.py` in `st.set_page_config`:

```python
    # "auto" statt "expanded": blendet die Sidebar auf kleinen Geräten aus und
    # zeigt sie auf Desktop — Streamlits Doku rät von "expanded" ausdrücklich ab,
    # weil die App auf dem Handy sonst schlecht aussieht.
    initial_sidebar_state="auto",
```

- [ ] **Schritt 4: Wirkung prüfen**

Run: `python3 scripts/ui_screenshot.py --width 390 --height 844 --out /tmp/mobil_nachher.png`
Erwartet: Sidebar ist zu, sichtbar sind Kopfbereich und Chat-Eingabe.
Beide Bilder ansehen und vergleichen.

- [ ] **Schritt 5: Committen**

```bash
git add scripts/ui_screenshot.py frontend/falken_ui.py
git commit -m "feat: Sidebar startet auf Mobil eingeklappt + Screenshot-Werkzeug"
```

---

### Aufgabe 2: Aktionszeile mit Beispielfragen und Verlauf

**Dateien:**
- Ändern: `frontend/falken_ui.py` — Konstante am Modulkopf (nach den Imports),
  Sidebar-Block (aktuell Zeilen 389–411), Bereich direkt vor `st.chat_input`

**Schnittstellen:**
- Konsumiert: `st.session_state["pending_q"]` (bestehende Mechanik, wird von
  `st.chat_input` weiter unten ausgelesen), `st.session_state.history`
- Erzeugt: `BEISPIELFRAGEN: list[str]` am Modulkopf — einzige Quelle der Fragen;
  `_aktionszeile() -> None`, aufzurufen unmittelbar vor `st.chat_input`

- [ ] **Schritt 1: Fragenliste als Konstante anlegen**

Direkt nach `st.set_page_config(...)` in `frontend/falken_ui.py` einfügen:

```python
# Beispielfragen — bewusst EINE Quelle: sie erscheinen unten in der Aktionszeile,
# nicht mehr zusätzlich in der Sidebar. Zwei Listen laufen sonst auseinander.
BEISPIELFRAGEN = [
    "Wann spielen die Falken diese Saison gegen Stuttgart?",
    "Auf welchem Tabellenplatz beendeten die Falken die Saison 2022/23?",
    "Wer war Topscorer der Falken in der Saison 2024/25?",
    "Wer war Trainer der Falken in der Saison 2018/19?",
    "Wer gewann die Halbfinale-Serie zwischen Falken und Hannover Scorpions 2024/25?",
    "Welches Ergebnis hatte das Spiel ECDC Memmingen vs Falken am 27.02.2026?",
    "In welcher Saison hatten die Falken die meisten Punkte aller Zeiten?",
    "Wie viele Saisons spielten die Falken in der DEL2?",
    "🌐 Wann hat der jetzige Besitzer der Tenno Sushi Bar bei den Falken gespielt?",
]
```

- [ ] **Schritt 2: Beispielfragen und Verlauf-Button aus der Sidebar entfernen**

In `frontend/falken_ui.py` diesen Block ersatzlos löschen (steht zwischen dem
ersten `st.divider()` und dem Abschnitt „Backend + Diagnose"):

```python
    # ── Beispielfragen oben (Hauptzweck) ─────────────────────────────────
    st.subheader("💡 Beispielfragen")
    examples = [ ... ]
    for q in examples:
        if st.button(q, key=f"ex_{hash(q)}", use_container_width=True):
            st.session_state["pending_q"] = q
            st.rerun()

    st.divider()
    if st.button("🗑 Verlauf löschen", use_container_width=True):
        st.session_state.history = []
        st.rerun()
```

Der `st.divider()` davor bleibt stehen, damit Kopfbereich und Backend-Kasten
weiterhin getrennt sind.

- [ ] **Schritt 3: Aktionszeile als Funktion ergänzen**

Vor der Zeile `q = st.chat_input("Frag HORST …")` einfügen:

```python
def _aktionszeile() -> None:
    """Beispielfragen + Verlauf direkt über dem Eingabefeld.

    WHY: In der Sidebar waren die Beispiele auf dem Handy nur über das
    Hamburger-Menü erreichbar — genau die Fragen, die neuen Nutzern zeigen,
    was HORST kann.
    """
    links, rechts = st.columns([4, 1])
    with links:
        with st.popover("💡 Beispielfragen", use_container_width=True):
            for frage in BEISPIELFRAGEN:
                if st.button(frage, key=f"bsp_{hash(frage)}", use_container_width=True):
                    st.session_state["pending_q"] = frage
                    st.rerun()
    with rechts:
        if st.button("🗑", help="Verlauf löschen", use_container_width=True):
            st.session_state.history = []
            st.rerun()


_aktionszeile()
q = st.chat_input("Frag HORST …")
```

- [ ] **Schritt 4: Doppelte Widget-Schlüssel ausschließen**

Run: `grep -c "ex_{hash" frontend/falken_ui.py`
Erwartet: `0` (alter Schlüssel ist weg, neu heißt er `bsp_`)

Run: `python3 -c "import ast; ast.parse(open('frontend/falken_ui.py').read()); print('Syntax ok')"`
Erwartet: `Syntax ok`

- [ ] **Schritt 5: Optisch prüfen**

Run: `python3 scripts/ui_screenshot.py --width 390 --height 844 --out /tmp/mobil_leiste.png`
Erwartet: Über dem Eingabefeld steht die Zeile „💡 Beispielfragen" mit dem
🗑-Button rechts daneben. Bild ansehen.

- [ ] **Schritt 6: Committen**

```bash
git add frontend/falken_ui.py
git commit -m "feat: Beispielfragen als Aktionszeile ueber dem Eingabefeld"
```

---

### Aufgabe 3: Mobile-Feinschliff per CSS

**Dateien:**
- Ändern: `frontend/falken_ui.py` — bestehender CSS-Block (beginnt mit dem
  Kommentar `/* Buttons (Sidebar examples) */`, aktuell um Zeile 123)

**Schnittstellen:**
- Konsumiert: die in Aufgabe 2 erzeugte Aktionszeile
- Erzeugt: keine neuen Namen

- [ ] **Schritt 1: CSS ergänzen**

Am Ende des bestehenden `<style>`-Blocks einfügen:

```css
/* Aktionszeile: Trigger im Falken-Rot, Daumen-taugliche Höhe */
div[data-testid="stPopover"] > button {
    min-height: 44px;
    font-weight: 600;
    border: 1px solid #c8102e;
    color: #c8102e;
}
div[data-testid="stPopover"] > button:hover {
    background: #c8102e;
    color: #ffffff;
    border-color: #c8102e;
}

/* Auf dem Handy zählt jede Zeile Höhe */
@media (max-width: 640px) {
    .block-container { padding-top: 1rem; padding-bottom: 0.5rem; }
    .falken-header img { height: 38px; }
    .falken-header h1 { font-size: 1.35rem; }
    .falken-header p { display: none; }
}
```

- [ ] **Schritt 2: Kopfbereich-Klassen gegenprüfen**

Run: `grep -n "falken-header" frontend/falken_ui.py | head -5`
Erwartet: Die Klasse existiert im HTML des Kopfbereichs. Falls die Unterzeile
dort anders heißt, den Selektor an den tatsächlichen Namen anpassen — nicht
raten, im Quelltext nachsehen.

- [ ] **Schritt 3: Optisch prüfen**

Run: `python3 scripts/ui_screenshot.py --width 390 --height 844 --out /tmp/mobil_css.png`
Erwartet: Kopfbereich kompakter, Trigger deutlich rot, Chat hat mehr Platz.

Run: `python3 scripts/ui_screenshot.py --width 1280 --height 900 --out /tmp/desktop_css.png`
Erwartet: Desktop unverändert mit offener Sidebar, Aktionszeile über der Eingabe.
Beide Bilder ansehen.

- [ ] **Schritt 4: Committen**

```bash
git add frontend/falken_ui.py
git commit -m "style: kompakterer Kopfbereich und groessere Tippflaechen auf dem Handy"
```

---

### Aufgabe 4: Abnahme und Auslieferung

**Dateien:**
- Keine Änderung — nur Prüfung und Deploy

**Schnittstellen:**
- Konsumiert: `scripts/ui_screenshot.py` aus Aufgabe 1,
  `scripts/deploy_streamlit.py` (vorhanden)

- [ ] **Schritt 1: Funktionsprüfung der Beispielfragen**

Run:
```bash
timeout 300 python3 -c "
from falken_kb.genai.orchestrator import answer
r = answer('Wann spielen die Falken diese Saison gegen Stuttgart?')
print(str(r.get('answer'))[:120])
"
```
Erwartet: Termine mit Testspiel-Kennzeichnung — belegt, dass die Fragen in der
Konstante weiterhin beantwortbar sind (Textgleichheit mit der alten Liste).

- [ ] **Schritt 2: Vollständigkeit der Liste prüfen**

Run: `python3 -c "
import re
src = open('frontend/falken_ui.py').read()
block = src.split('BEISPIELFRAGEN = [',1)[1].split(']',1)[0]
print(len(re.findall(r'\"([^\"]+)\"', block)), 'Fragen')"`
Erwartet: `9 Fragen`

- [ ] **Schritt 3: Screenshots final ansehen**

Run: `python3 scripts/ui_screenshot.py --width 390 --height 844 --out /tmp/abnahme_mobil.png`
Run: `python3 scripts/ui_screenshot.py --width 1280 --height 900 --out /tmp/abnahme_desktop.png`
Erwartet, im Bild zu sehen: Handy zeigt Chat + Aktionszeile ohne Sidebar;
Desktop zeigt Sidebar mit Backend/Diagnose, aber ohne Beispielfragen-Liste.
Ist das Popover-Panel auf 390 px abgeschnitten, hier stoppen und melden —
nicht schöngeredet ausliefern (siehe Risiko in der Spec).

- [ ] **Schritt 4: Ausliefern und Live-Stand bestätigen**

Run: `python3 scripts/deploy_streamlit.py --minutes 8`
Erwartet: `✓ Live-Stand entspricht jetzt <Stempel>`

- [ ] **Schritt 5: Committen**

```bash
git add -A
git commit -m "chore: Abnahme der mobilen Beispielfragen-Leiste"
```

---

## Selbstprüfung des Plans

**Spec-Abdeckung:** `initial_sidebar_state="auto"` → Aufgabe 1. Konstante +
Popover-Zeile + Verlauf-Button unten + Entfernen aus der Sidebar → Aufgabe 2.
Falken-Rot, 44 px, Media-Query → Aufgabe 3. Abnahme bei 375–390 px und Desktop,
Klick-Test, Deploy-Stempel → Aufgabe 4. Backend und Diagnose bleiben unberührt
(in keiner Aufgabe angefasst). Das Popover-Risiko ist in Aufgabe 4, Schritt 3
als Abbruchbedingung hinterlegt.

**Platzhalter:** keine — jeder Schritt nennt Datei, Code und Prüfbefehl.

**Namensgleichheit:** `BEISPIELFRAGEN` und `_aktionszeile()` werden in Aufgabe 2
definiert und in Aufgabe 3 und 4 unter genau diesen Namen verwendet; der
Widget-Schlüssel heißt durchgängig `bsp_`.
