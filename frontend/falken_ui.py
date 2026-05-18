"""UI für die Falken-Wissensdatenbank — schickes Falken-Design.

Aufruf lokal:
    streamlit run frontend/falken_ui.py
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st  # noqa: E402

st.set_page_config(
    page_title="Falken-KB",
    page_icon="🦅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────────────────────────────────────
# Secrets → env (Streamlit Cloud + lokal). MUSS vor falken_kb.config laufen.
# ──────────────────────────────────────────────────────────────────────────────
def _load_secrets_into_env() -> dict[str, str]:
    """Liest st.secrets in os.environ. Returnt dict der gesetzten keys (für Debug)."""
    loaded: dict[str, str] = {}
    try:
        secrets = st.secrets
    except Exception:
        return loaded
    try:
        keys = list(secrets.keys())
    except Exception:
        return loaded
    for k in keys:
        try:
            v = secrets[k]
        except Exception:
            continue
        if isinstance(v, (str, int, float, bool)):
            os.environ[k] = str(v)  # OVERRIDE (statt setdefault!) — Streamlit-Secrets sind die Wahrheit
            loaded[k] = "***" if "key" in k.lower() or "password" in k.lower() or "token" in k.lower() else str(v)[:50]
    if "default" in keys:
        try:
            for k, v in dict(secrets["default"]).items():
                if isinstance(v, (str, int, float, bool)):
                    os.environ[k] = str(v)
                    loaded[k] = "***" if "key" in k.lower() or "password" in k.lower() else str(v)[:50]
        except Exception:
            pass
    return loaded


_SECRETS_LOADED = _load_secrets_into_env()

from falken_kb.config import settings  # noqa: E402
from falken_kb.genai.orchestrator import answer as kb_answer  # noqa: E402


# ──────────────────────────────────────────────────────────────────────────────
# FALKEN-DESIGN: Custom CSS — schwarz / Falken-Gold / weiß
# ──────────────────────────────────────────────────────────────────────────────
FALKEN_GOLD = "#F5B81C"  # offizielles Falken-Gold
FALKEN_BLACK = "#0A0A0A"
LOGO_URL = "https://www.heilbronner-falken.de/wp-content/uploads/2023/02/HNECF_Logo-01-150x150.png"

st.markdown(
    f"""
    <style>
    /* Background dark */
    .stApp {{
        background: linear-gradient(180deg, #0a0a0a 0%, #1a1a1a 100%);
        color: #f0f0f0;
    }}
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: #000000;
        border-right: 2px solid {FALKEN_GOLD};
    }}
    section[data-testid="stSidebar"] * {{
        color: #f0f0f0 !important;
    }}
    /* Headlines */
    h1, h2, h3 {{
        color: {FALKEN_GOLD} !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    /* Buttons (Beispielfragen etc.) */
    .stButton > button {{
        background: rgba(245, 184, 28, 0.08);
        color: #f0f0f0 !important;
        border: 1px solid rgba(245, 184, 28, 0.3);
        border-radius: 8px;
        transition: all 0.15s ease;
        text-align: left;
        font-size: 0.85rem;
    }}
    .stButton > button:hover {{
        background: {FALKEN_GOLD};
        color: {FALKEN_BLACK} !important;
        border-color: {FALKEN_GOLD};
        transform: translateY(-1px);
    }}
    /* Primary button (Anmelden, Submit) */
    .stButton > button[kind="primary"] {{
        background: {FALKEN_GOLD};
        color: {FALKEN_BLACK} !important;
        border: none;
        font-weight: 700;
    }}
    .stButton > button[kind="primary"]:hover {{
        background: #ffcb3a;
    }}
    /* Chat-Messages */
    [data-testid="stChatMessage"] {{
        background: rgba(255,255,255,0.03);
        border-left: 3px solid {FALKEN_GOLD};
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }}
    /* Code-Blocks */
    .stCodeBlock, code {{
        background: #0a0a0a !important;
        border: 1px solid rgba(245, 184, 28, 0.2);
    }}
    /* Input */
    .stTextInput input, .stChatInput textarea {{
        background: #1a1a1a !important;
        color: #f0f0f0 !important;
        border: 1px solid rgba(245, 184, 28, 0.4) !important;
    }}
    /* Expander */
    .streamlit-expanderHeader {{
        background: rgba(245, 184, 28, 0.05);
        border-radius: 6px;
        color: {FALKEN_GOLD} !important;
    }}
    /* Divider */
    hr {{
        border-color: rgba(245, 184, 28, 0.2) !important;
    }}
    /* Falken Branding Header */
    .falken-header {{
        display: flex;
        align-items: center;
        gap: 1rem;
        padding: 1rem 0;
        border-bottom: 2px solid {FALKEN_GOLD};
        margin-bottom: 1.5rem;
    }}
    .falken-header img {{
        width: 64px;
        height: 64px;
    }}
    .falken-header-text h1 {{
        margin: 0;
        font-size: 1.8rem;
    }}
    .falken-header-text p {{
        margin: 0;
        color: #aaa;
        font-size: 0.9rem;
    }}
    /* Sidebar-Logo */
    .sidebar-logo {{
        text-align: center;
        padding: 1rem 0;
    }}
    .sidebar-logo img {{
        width: 96px;
        filter: drop-shadow(0 2px 8px rgba(245, 184, 28, 0.4));
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ──────────────────────────────────────────────────────────────────────────────
# Auth-Wrapper
# ──────────────────────────────────────────────────────────────────────────────
def _get_app_password() -> str | None:
    env_pw = os.environ.get("APP_PASSWORD")
    if env_pw:
        return env_pw
    try:
        return st.secrets.get("app_password")
    except Exception:
        return None


def _password_protect() -> bool:
    expected = _get_app_password()
    if not expected:
        return True
    if st.session_state.get("authenticated"):
        return True
    st.markdown(
        f"""<div class="falken-header">
        <img src="{LOGO_URL}" alt="Falken">
        <div class="falken-header-text"><h1>Falken-Wissensdatenbank</h1><p>Bitte Passwort eingeben</p></div>
        </div>""",
        unsafe_allow_html=True,
    )
    pw = st.text_input("Passwort", type="password", label_visibility="collapsed", placeholder="Passwort eingeben…")
    if st.button("Anmelden", type="primary") and pw == expected:
        st.session_state["authenticated"] = True
        st.rerun()
    elif pw and pw != expected:
        st.error("Falsches Passwort")
    return False


if not _password_protect():
    st.stop()


# ──────────────────────────────────────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}" alt="Falken-Logo"></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; margin-top:0;'>Falken-KB</h2>", unsafe_allow_html=True)
    st.caption("Heilbronner Falken — GenAI-Wissensdatenbank")

    st.divider()
    st.subheader("⚙ Backend")

    def _device_label(url: str) -> str:
        u = (url or "").lower()
        if "pgxapi.siller.io" in u: return "DGX (siller.io, self-hosted)"
        if "openrouter" in u: return "OpenRouter (cloud)"
        if "openai.com" in u: return "OpenAI (cloud)"
        return "Custom Endpoint"

    st.code(
        f"Gerät:      {_device_label(settings.dgx_base_url)}\n"
        f"Chat:       {settings.dgx_chat_model or '(leer)'}\n"
        f"Embeddings: {settings.dgx_embed_model or '(leer)'} ({settings.dgx_embed_dim}d)",
        language="text",
    )

    # Debug-Sektion: hilft wenn secrets nicht ankommen
    with st.expander("🔧 Diagnose"):
        st.markdown("**Aus st.secrets/env geladen:**")
        if _SECRETS_LOADED:
            for k, v in sorted(_SECRETS_LOADED.items()):
                st.text(f"  {k} = {v}")
        else:
            st.warning("Keine Secrets geladen! Bitte in Streamlit Cloud → Settings → Secrets eintragen.")
        st.markdown("**Aktive Config:**")
        st.text(f"  DGX_API_KEY gesetzt: {'✓' if settings.dgx_api_key else '✗'}")
        st.text(f"  SUPABASE_SERVICE_ROLE_KEY gesetzt: {'✓' if settings.supabase_service_role_key else '✗'}")

    st.divider()
    st.subheader("💡 Beispielfragen")
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
# Main
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""<div class="falken-header">
    <img src="{LOGO_URL}" alt="Falken">
    <div class="falken-header-text">
        <h1>Frag die Falken-Wissensdatenbank</h1>
        <p>Eishockey-Wissen aus 45+ Jahren Vereinsgeschichte — Saisons · Spiele · Trainer · Spielerstatistiken · Playoffs · News</p>
    </div>
    </div>""",
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []

prefilled = st.session_state.pop("pending_q", "")

q = st.chat_input("Stell deine Falken-Frage…")
if not q and prefilled:
    q = prefilled

# Render history
for entry in st.session_state.history:
    with st.chat_message("user", avatar="👤"):
        st.markdown(entry["q"])
    with st.chat_message("assistant", avatar="🦅"):
        result = entry["result"]
        st.markdown(result.get("answer", "(keine Antwort)"))
        cat = result.get("category", "?")
        t_sec = entry.get("t_sec", 0)
        st.caption(f"📂 `{cat}` · ⏱ {t_sec:.1f}s")
        sql = result.get("sql")
        if sql:
            with st.expander("🔎 SQL"):
                st.code(sql, language="sql")
        rows = result.get("rows")
        if rows:
            with st.expander(f"📊 DB-Resultat ({len(rows)} Zeilen)"):
                st.dataframe(rows, use_container_width=True)
        sources = result.get("sources")
        if sources:
            with st.expander(f"📰 Quellen ({len(sources)})"):
                for s in sources:
                    st.write(f"- {s.get('title', '?')} ({s.get('source', '?')})")

# Neue Frage
if q:
    with st.chat_message("user", avatar="👤"):
        st.markdown(q)
    with st.chat_message("assistant", avatar="🦅"):
        with st.spinner("🦅 Falken-Daten werden durchsucht…"):
            t0 = time.time()
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
        st.caption(f"📂 `{result.get('category', '?')}` · ⏱ {t_sec:.1f}s")
        sql = result.get("sql")
        if sql:
            with st.expander("🔎 SQL"):
                st.code(sql, language="sql")
        rows = result.get("rows")
        if rows:
            with st.expander(f"📊 DB-Resultat ({len(rows)} Zeilen)"):
                st.dataframe(rows, use_container_width=True)
        sources = result.get("sources")
        if sources:
            with st.expander(f"📰 Quellen ({len(sources)})"):
                for s in sources:
                    st.write(f"- {s.get('title', '?')} ({s.get('source', '?')})")
    st.session_state.history.append({"q": q, "result": result, "t_sec": t_sec})
