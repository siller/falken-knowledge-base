# Beispielfragen auf Mobil erreichbar machen

**Stand:** 25.07.2026 · **Datei:** `frontend/falken_ui.py` · **Streamlit:** 1.37

## Problem

Auf dem Handy startet die App mit ausgeklappter Sidebar. Sichtbar sind damit
zuerst Beispielfragen, Backend-Infos und Diagnose — nicht der Chat. Wer eine
Beispielfrage antippen will, muss über das Hamburger-Menü zurück in die
Sidebar. Streamlits eigene Dokumentation rät von unserer Einstellung ab:
`initial_sidebar_state="expanded"` lasse die App „on mobile" schlecht aussehen.

## Lösung

Eine Aktionszeile direkt über dem Eingabefeld, und die Sidebar startet auf
kleinen Geräten eingeklappt.

```
┌────────────────────────┐   angetippt:
│ [Chatverlauf]          │   ┌──────────────────┐
│                        │   │ Spiele vs Stuttgart│
│                        │   │ Tabellenplatz 22/23│
├────────────────────────┤   │ Topscorer 24/25    │
│ 💡 Beispielfragen  │ 🗑 │   │ …                  │
│ [ Frag HORST …       ] │   └──────────────────┘
└────────────────────────┘
```

## Entscheidungen

| Punkt | Entscheidung | Begründung |
|---|---|---|
| Sidebar-Start | `initial_sidebar_state="auto"` | Blendet die Sidebar laut Doku auf kleinen Geräten aus, auf Desktop bleibt sie offen — eine Einstellung, kein Sonderfall im Code |
| Umsetzung | `st.popover` (Bordmittel) | Kein CSS gegen Streamlits DOM, überlebt Updates; `st.pills` gibt es erst ab 1.40 |
| Fragenliste | Konstante am Modulkopf | Bisher inline in der Sidebar; die Liste soll es nur einmal geben |
| „Verlauf löschen" | wandert nach unten, verschwindet aus der Sidebar | Häufig gebraucht, gehört neben die Eingabe; doppelte Bedienelemente laufen auseinander |
| Backend + Diagnose | bleiben in der Sidebar | Im Stadion über das Menü erreichbar, aber nicht im Weg |
| Desktop | bekommt dieselbe Aktionszeile | Ein Codepfad statt zweier Zustände, die auseinanderdriften |

## Umsetzung im Detail

1. **`st.set_page_config`**: `initial_sidebar_state` von `"expanded"` auf `"auto"`.
2. **`BEISPIELFRAGEN`** als Konstante am Modulkopf; die Sidebar-Schleife entfällt.
3. **Aktionszeile** unmittelbar vor `st.chat_input`:
   `st.columns([4, 1])` → links `st.popover("💡 Beispielfragen", use_container_width=True)`
   mit je einem Button pro Frage (`use_container_width=True`), rechts der
   Verlauf-Button. Klick setzt wie bisher `st.session_state["pending_q"]` und
   löst `st.rerun()` aus — die bestehende Mechanik bleibt unverändert.
4. **CSS**: Trigger in Falken-Rot, Mindesthöhe 44 px (Daumengröße); unter 640 px
   kleinerer Header und weniger Außenabstand.

## Abnahme

* Handy-Breite (375 px) und Desktop lokal prüfen: Startbild ist der Chat,
  Panel öffnet vollständig und wird nicht abgeschnitten.
* Eine Beispielfrage antippen → Frage wird gestellt, Panel schließt sich.
* „Verlauf löschen" leert den Verlauf, in der Sidebar taucht er nicht mehr auf.
* Desktop: Sidebar weiterhin offen, Backend und Diagnose unverändert.
* Danach `scripts/deploy_streamlit.py` — live erst, wenn der Stempel ankommt.

## Bekanntes Risiko

Streamlit positioniert das Popover-Panel selbst. Auf sehr schmalen Schirmen
kann es knapp werden. Fällt das im Test auf, wird es per CSS gefangen; trägt
das nicht, geht die Rückmeldung an den Nutzer statt einer schöngeredeten
Auslieferung.

## Nicht Teil dieser Änderung

Chatblasen, Schriftgrößen und die SQL-/Quellen-Aufklapper bleiben, wie sie
sind — als Ärgernis genannt wurden Sidebar und Erreichbarkeit der Beispiele,
und der Rest der Oberfläche funktioniert auf dem Desktop.
