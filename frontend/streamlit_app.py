"""Streamlit-Chat-Frontend für die Falken-Wissensdatenbank.

Starten: `streamlit run frontend/streamlit_app.py`
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

# Repo-Root in sys.path damit `falken_kb` importierbar ist
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st  # noqa: E402

from falken_kb.genai.orchestrator import answer  # noqa: E402

st.set_page_config(page_title="Falken Wissensdatenbank", page_icon="🦅", layout="wide")

st.title("🦅 Heilbronner Falken — Wissensdatenbank")
st.caption("Powered by DGX / Gemma-4 + Supabase + hockeydata-API")

with st.sidebar:
    st.subheader("Beispielfragen")
    samples = {
        "🏆 Aktuelle Saison": [
            "Auf welchem Platz stehen die Falken aktuell?",
            "Welches war das höchste Tor-Ergebnis der Falken in 2025/26?",
            "Wer waren die Topscorer der Falken in der aktuellen Saison?",
        ],
        "📜 Historie": [
            "Wer war Topscorer der Falken in 2018/19?",
            "Wann sind die Falken zuletzt aus der DEL2 abgestiegen?",
            "Wer war Trainer der Falken in der Abstiegssaison 2022/23?",
            "In welcher Saison hatten die Falken die meisten Punkte?",
        ],
        "🥅 Playoffs": [
            "Welche Falken-Playoff-Serien gab es in den letzten 10 Jahren?",
            "Gegen wen haben die Falken 2021/22 im Halbfinale verloren?",
            "Wer hat die Falken aus den Playdowns 2022/23 in die Oberliga geschickt?",
        ],
        "🏟️ Spiele": [
            "Welche Spiele hat es zwischen Falken und Bayreuth in den letzten Jahren gegeben?",
            "Wer hat gegen wen am 06.02.2026 mit 11:3 gewonnen?",
            "Wann war das letzte Heimspiel der Falken in der DEL2 22/23?",
        ],
        "📈 Trends": [
            "Wie entwickelten sich die Punkte der Falken über die letzten Saisons?",
            "Wie viele DEL2-Spiele haben die Falken insgesamt gespielt?",
        ],
        "🌐 Narrative": [
            "Wie war die DEL2-Saison 2022/23 generell?",
            "Was passierte beim Falken-Abstieg 2023?",
        ],
    }
    for group, qs in samples.items():
        st.markdown(f"**{group}**")
        for q in qs:
            if st.button(q, use_container_width=True, key=q):
                st.session_state["question"] = q

if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Pending-Frage aus Sidebar-Klick übernehmen
if pending := st.session_state.pop("question", None):
    st.session_state["messages"].append({"role": "user", "content": pending})

# History rendern
for m in st.session_state["messages"]:
    with st.chat_message(m["role"]):
        st.markdown(m["content"])
        if m.get("details"):
            with st.expander("Details (SQL / Quellen / Klassifikation)"):
                st.json(m["details"])
        if m.get("chart_spec"):
            st.vega_lite_chart(m["chart_spec"], use_container_width=True)

# Wenn letzte Nachricht eine User-Frage ist und noch keine Antwort folgt → antworten
if st.session_state["messages"] and st.session_state["messages"][-1]["role"] == "user":
    with st.chat_message("assistant"):
        with st.spinner("Denke nach …"):
            try:
                result = answer(st.session_state["messages"][-1]["content"])
                answer_text = result.pop("answer", "(keine Antwort)")
                chart = result.pop("chart_spec", None)
                st.markdown(answer_text)
                if chart:
                    st.vega_lite_chart(chart, use_container_width=True)
                with st.expander("Details (SQL / Quellen / Klassifikation)"):
                    st.json(result)
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": answer_text,
                    "details": result,
                    "chart_spec": chart,
                })
            except Exception as e:
                st.error(f"Fehler: {e}")
                st.session_state["messages"].append({
                    "role": "assistant",
                    "content": f"⚠️ Fehler: {e}",
                })

# Eingabefeld
if q := st.chat_input("Stelle eine Frage zu den Heilbronner Falken …"):
    st.session_state["messages"].append({"role": "user", "content": q})
    st.rerun()
