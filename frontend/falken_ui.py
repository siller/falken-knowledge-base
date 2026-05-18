"""Mini-UI für die Falken-Wissensdatenbank.

Aufruf:
    cd /Users/marksiller/Dropbox/1Privat/_SSO_KI_/FalkenDaten/_Code_/falken-knowledge-base
    streamlit run frontend/falken_ui.py

Optional: per Env-Variable das Backend wechseln (Default = OpenRouter, was in .env steht):
    DGX_BASE_URL=https://pgxapi.siller.io/v1 DGX_API_KEY=... DGX_CHAT_MODEL=gemma \\
      streamlit run frontend/falken_ui.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

# Repo-Root in PATH einbinden (damit `falken_kb.*` importierbar ist)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

# IMMER zuerst — muss vor jedem anderen st.* call stehen.
st.set_page_config(page_title="Falken-Wissensdatenbank", page_icon="🏒", layout="wide")

# Streamlit-Cloud: secrets aus st.secrets in os.environ überführen, BEVOR
# falken_kb.config geladen wird. Lokal (ohne secrets.toml): überspringen.
_SECRETS_PATHS = [
    Path.home() / ".streamlit" / "secrets.toml",
    ROOT / ".streamlit" / "secrets.toml",
]
if any(p.exists() for p in _SECRETS_PATHS):
    try:
        secrets = st.secrets
        if "default" in secrets:
            secrets = secrets["default"]
        for key in secrets:
            if isinstance(secrets[key], (str, int, float, bool)):
                os.environ.setdefault(key, str(secrets[key]))
    except Exception:
        pass  # silent fallback — env-vars / .env weiter genutzt

from falken_kb.config import settings  # noqa: E402
from falken_kb.genai.orchestrator import answer as kb_answer  # noqa: E402


def _get_app_password() -> str | None:
    """APP_PASSWORD aus env ODER secrets, ohne Warning wenn nichts da ist."""
    env_pw = os.environ.get("APP_PASSWORD")
    if env_pw:
        return env_pw
    if any(p.exists() for p in _SECRETS_PATHS):
        try:
            return st.secrets.get("app_password")
        except Exception:
            return None
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Auth-Wrapper: Shared-Password-Schutz (für Streamlit Cloud + Team-Zugriff)
# Passwort kommt aus secrets[\"app_password\"] oder env APP_PASSWORD.
# Wenn kein Passwort gesetzt → öffentlich (local dev).
# ──────────────────────────────────────────────────────────────────────────────
def _password_protect() -> bool:
    expected = _get_app_password()
    if not expected:
        return True  # kein Passwort konfiguriert → frei
    if st.session_state.get("authenticated"):
        return True
    st.title("🏒 Falken-Wissensdatenbank")
    st.caption("Bitte Passwort eingeben")
    pw = st.text_input("Passwort", type="password")
    if st.button("Anmelden", type="primary") and pw == expected:
        st.session_state["authenticated"] = True
        st.rerun()
    elif pw and pw != expected:
        st.error("Falsches Passwort")
    return False


if not _password_protect():
    st.stop()

# ──────────────────────────────────────────────────────────────────────────────
# Sidebar: Backend-Info + Beispielfragen
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🏒 Falken-KB")
    st.caption("Heilbronner Falken — GenAI-Wissensdatenbank")

    st.subheader("Backend")
    def _device_label(url: str) -> str:
        u = (url or "").lower()
        if "pgxapi.siller.io" in u: return "DGX (siller.io, self-hosted)"
        if "openrouter" in u: return "OpenRouter (cloud)"
        if "openai.com" in u: return "OpenAI"
        return "Custom Endpoint"
    st.code(
        f"Gerät:      {_device_label(settings.dgx_base_url)}\n"
        f"Chat:       {settings.dgx_chat_model}\n"
        f"Embeddings: {settings.dgx_embed_model} ({settings.dgx_embed_dim}d)",
        language="text",
    )

    st.divider()
    st.subheader("Beispielfragen")
    examples = [
        "Auf welchem Tabellenplatz beendeten die Falken die Saison 2022/23?",
        "Wer war Topscorer der Falken in der Saison 2024/25?",
        "Wer war Trainer der Falken in der Saison 2018/19?",
        "Wer gewann die Halbfinale-Serie zwischen Falken und Hannover Scorpions 2024/25?",
        "Welches Ergebnis hatte das Spiel ECDC Memmingen vs Falken am 27.02.2026?",
        "In welcher Saison hatten die Falken die meisten Punkte aller Zeiten?",
        "Wie viele Saisons spielten die Falken in der DEL2?",
    ]
    for q in examples:
        if st.button(q, key=f"ex_{hash(q)}", use_container_width=True):
            st.session_state["pending_q"] = q
            st.rerun()

    st.divider()
    if st.button("🗑 Verlauf löschen", use_container_width=True):
        st.session_state.history = []
        st.rerun()


# ──────────────────────────────────────────────────────────────────────────────
# Main: Chat
# ──────────────────────────────────────────────────────────────────────────────
st.title("Frag die Falken-Wissensdatenbank")
st.caption(
    "Tippe eine Frage zu Heilbronner-Falken-Eishockey ein — Saisons, Spiele, "
    "Trainer, Spielerstatistiken, Playoffs. Antwort kommt aus der lokalen DB "
    "via GenAI-Pipeline (kein Internet-Lookup)."
)

if "history" not in st.session_state:
    st.session_state.history = []  # list of {q, result, t_sec}

# Wenn Beispielfrage geklickt, pre-fill
prefilled = st.session_state.pop("pending_q", "")

q = st.chat_input("Frage eingeben...")
if not q and prefilled:
    q = prefilled

# Render existing history
for entry in st.session_state.history:
    with st.chat_message("user"):
        st.markdown(entry["q"])
    with st.chat_message("assistant"):
        result = entry["result"]
        st.markdown(result.get("answer", "(keine Antwort)"))
        cat = result.get("category", "?")
        t_sec = entry.get("t_sec", "?")
        st.caption(f"Kategorie: `{cat}` · Antwortzeit: {t_sec:.1f}s")
        sql = result.get("sql")
        if sql:
            with st.expander("SQL"):
                st.code(sql, language="sql")
        rows = result.get("rows")
        if rows:
            with st.expander(f"DB-Resultat ({len(rows)} Zeilen)"):
                st.dataframe(rows, use_container_width=True)
        sources = result.get("sources")
        if sources:
            with st.expander(f"Quellen ({len(sources)})"):
                for s in sources:
                    st.write(f"- {s.get('title', '?')} ({s.get('source', '?')})")

# Process new question
if q:
    with st.chat_message("user"):
        st.markdown(q)
    with st.chat_message("assistant"):
        with st.spinner("Frage wird verarbeitet (Klassifikation → SQL/RAG → Synthese)..."):
            t0 = time.time()
            # Multi-Turn: wenn vorige Frage da war, als Kontext mitgeben
            effective_q = q
            if st.session_state.history:
                last = st.session_state.history[-1]
                last_q = last["q"]
                last_a = last["result"].get("answer", "")[:300]
                effective_q = (
                    f"VORHERIGE FRAGE: {last_q}\n"
                    f"VORHERIGE ANTWORT: {last_a}\n\n"
                    f"FOLGEFRAGE (bezieht sich auf den obigen Kontext, "
                    f"resolve Pronomen + 'besser/schlechter/auch' anhand des Kontexts): {q}"
                )
            try:
                result = kb_answer(effective_q)
                t_sec = time.time() - t0
            except Exception as e:
                st.error(f"Fehler: {e}")
                result = {"answer": f"Fehler: {e}", "category": "error"}
                t_sec = time.time() - t0
        st.markdown(result.get("answer", "(keine Antwort)"))
        st.caption(f"Kategorie: `{result.get('category', '?')}` · Antwortzeit: {t_sec:.1f}s")
        sql = result.get("sql")
        if sql:
            with st.expander("SQL"):
                st.code(sql, language="sql")
        rows = result.get("rows")
        if rows:
            with st.expander(f"DB-Resultat ({len(rows)} Zeilen)"):
                st.dataframe(rows, use_container_width=True)
        sources = result.get("sources")
        if sources:
            with st.expander(f"Quellen ({len(sources)})"):
                for s in sources:
                    st.write(f"- {s.get('title', '?')} ({s.get('source', '?')})")
    st.session_state.history.append({"q": q, "result": result, "t_sec": t_sec})
