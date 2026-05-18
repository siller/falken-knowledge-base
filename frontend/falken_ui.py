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
    page_title="HORST — Falken-Wissensdatenbank",
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

from falken_kb.config import settings, reload_settings  # noqa: E402
# Fix für Streamlit-Cloud-Cache: settings ggf. mit aktuellen env-vars neu laden.
# Falls config.py beim ersten Import noch keine Cloud-Secrets in env hatte,
# wären settings.* stale. reload_settings() mutiert das Singleton in-place.
reload_settings()
from falken_kb.genai.orchestrator import answer as kb_answer  # noqa: E402


# ──────────────────────────────────────────────────────────────────────────────
# FALKEN-DESIGN — Farben aus Sponsoring-Konzept (hell, modern)
# Rot/Navy/Blau auf hellem Hintergrund, Apple-System-Font
# ──────────────────────────────────────────────────────────────────────────────
FALKEN_RED = "#D30A10"
FALKEN_RED_DARK = "#A50000"
FALKEN_NAVY = "#001D3D"
FALKEN_BLUE = "#003C79"
FALKEN_BLUE_LIGHT = "#004A98"
FALKEN_GOLD = "#C9A227"
BG_LIGHT = "#F4F6F9"
SURFACE = "#FFFFFF"
TEXT = "#0E1A2B"
TEXT_MUTED = "#4A5A70"
BORDER = "#E2E7EF"
LOGO_URL = "https://www.heilbronner-falken.de/wp-content/uploads/2023/02/HNECF_Logo-01-150x150.png"

st.markdown(
    f"""
    <style>
    /* Font + Base */
    html, body, .stApp, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, Roboto, sans-serif !important;
    }}
    .stApp {{
        background: {BG_LIGHT};
        color: {TEXT};
    }}
    /* Sidebar */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {FALKEN_NAVY} 0%, {FALKEN_BLUE} 100%);
        border-right: none;
    }}
    section[data-testid="stSidebar"] * {{
        color: rgba(255,255,255,0.92) !important;
    }}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: white !important;
    }}
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {{
        color: rgba(255,255,255,0.65) !important;
    }}
    /* Main Headings */
    .stApp h1, .stApp h2, .stApp h3 {{
        color: {FALKEN_NAVY} !important;
        font-weight: 800;
        letter-spacing: -0.02em;
    }}
    .stApp h1 .accent, .stApp h2 .accent {{
        color: {FALKEN_RED};
    }}
    /* Buttons (Sidebar examples) */
    section[data-testid="stSidebar"] .stButton > button {{
        background: rgba(255,255,255,0.08);
        color: white !important;
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 10px;
        text-align: left;
        font-size: 0.85rem;
        transition: all 0.15s ease;
        padding: 0.5rem 0.75rem;
    }}
    section[data-testid="stSidebar"] .stButton > button:hover {{
        background: {FALKEN_RED};
        border-color: {FALKEN_RED};
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(211, 10, 16, 0.35);
    }}
    /* Primary buttons (Main area: Anmelden) */
    .stApp .stButton > button[kind="primary"] {{
        background: {FALKEN_RED};
        color: white !important;
        border: none;
        font-weight: 700;
        padding: 0.6rem 1.5rem;
        border-radius: 8px;
        transition: all 0.15s ease;
    }}
    .stApp .stButton > button[kind="primary"]:hover {{
        background: {FALKEN_RED_DARK};
        transform: translateY(-1px);
        box-shadow: 0 4px 16px rgba(211, 10, 16, 0.4);
    }}
    /* Chat-Messages */
    [data-testid="stChatMessage"] {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-left: 4px solid {FALKEN_RED};
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
        box-shadow: 0 2px 8px rgba(14, 26, 43, 0.04);
    }}
    [data-testid="stChatMessage"][data-testid*="user"] {{
        border-left-color: {FALKEN_BLUE};
        background: rgba(0, 60, 121, 0.04);
    }}
    /* Code-Blocks */
    pre, .stCodeBlock {{
        background: {FALKEN_NAVY} !important;
        border-radius: 8px;
        border: 1px solid {FALKEN_BLUE};
    }}
    pre code, .stCodeBlock code {{
        color: #e8eef7 !important;
    }}
    /* Inline code */
    .stApp code:not(pre code) {{
        background: rgba(211, 10, 16, 0.08);
        color: {FALKEN_RED_DARK};
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.85em;
    }}
    /* Input */
    .stTextInput input, .stChatInput textarea, [data-testid="stChatInput"] textarea {{
        background: {SURFACE} !important;
        color: {TEXT} !important;
        border: 1.5px solid {BORDER} !important;
        border-radius: 10px !important;
    }}
    .stTextInput input:focus, .stChatInput textarea:focus {{
        border-color: {FALKEN_RED} !important;
        box-shadow: 0 0 0 3px rgba(211, 10, 16, 0.1) !important;
    }}
    /* Expander */
    [data-testid="stExpander"] {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-radius: 8px;
    }}
    [data-testid="stExpander"] summary {{
        color: {FALKEN_NAVY} !important;
        font-weight: 600;
    }}
    /* Divider */
    hr {{
        border-color: {BORDER} !important;
    }}
    /* Caption */
    .stCaption, small, [data-testid="stCaptionContainer"] {{
        color: {TEXT_MUTED} !important;
    }}
    /* Spinner color */
    .stSpinner > div {{
        border-top-color: {FALKEN_RED} !important;
    }}
    /* Dataframe */
    .stDataFrame {{
        border-radius: 8px;
        overflow: hidden;
    }}
    /* Falken Branding Header */
    .falken-header {{
        display: flex;
        align-items: center;
        gap: 1.25rem;
        padding: 1.25rem 1.5rem;
        background: linear-gradient(135deg, {FALKEN_NAVY} 0%, {FALKEN_BLUE_LIGHT} 100%);
        border-radius: 14px;
        margin-bottom: 1.75rem;
        box-shadow: 0 8px 24px rgba(0, 29, 61, 0.15);
        position: relative;
        overflow: hidden;
    }}
    .falken-header::before {{
        content: "";
        position: absolute;
        top: 0; right: 0; bottom: 0; left: 0;
        background: radial-gradient(circle at 90% 30%, rgba(211, 10, 16, 0.35) 0%, transparent 55%);
        pointer-events: none;
    }}
    .falken-header img {{
        width: 72px;
        height: 72px;
        position: relative;
        z-index: 1;
        filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3));
    }}
    .falken-header-text {{
        position: relative;
        z-index: 1;
    }}
    .falken-header-text h1 {{
        margin: 0 !important;
        font-size: 1.85rem;
        color: white !important;
        font-weight: 800;
        letter-spacing: -0.02em;
    }}
    .falken-header-text h1 .accent {{
        color: #ffb3b3 !important;
    }}
    .falken-header-text p {{
        margin: 0.35rem 0 0;
        color: rgba(255,255,255,0.85);
        font-size: 0.95rem;
    }}
    /* Sidebar-Logo Container */
    .sidebar-logo {{
        text-align: center;
        padding: 1rem 0 0.5rem;
    }}
    .sidebar-logo img {{
        width: 88px;
        filter: drop-shadow(0 4px 12px rgba(0,0,0,0.3));
    }}
    /* Reduce default top padding */
    .block-container {{
        padding-top: 2rem !important;
    }}
    /* Sidebar Code-Block (Backend-Info) */
    section[data-testid="stSidebar"] pre,
    section[data-testid="stSidebar"] .stCodeBlock {{
        background: rgba(0,0,0,0.25) !important;
        border-color: rgba(255,255,255,0.12) !important;
    }}
    section[data-testid="stSidebar"] pre code {{
        color: rgba(255,255,255,0.9) !important;
    }}
    /* Error/Warning Boxes */
    [data-testid="stAlert"] {{
        border-radius: 10px;
        border-left-width: 4px;
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
        <div class="falken-header-text">
            <h1>HORST <span class="accent">·</span> Falken-KB</h1>
            <p>Der Falkenhorst des Falken-Wissens · Bitte Passwort eingeben</p>
        </div>
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
def _device_label(url: str) -> str:
    u = (url or "").lower()
    if "pgxapi.siller.io" in u: return "DGX (siller.io, self-hosted)"
    if "openrouter" in u: return "OpenRouter (cloud)"
    if "openai.com" in u: return "OpenAI (cloud)"
    return "Custom Endpoint"


with st.sidebar:
    # ── Brand-Header oben ────────────────────────────────────────────────
    st.markdown(f'<div class="sidebar-logo"><img src="{LOGO_URL}" alt="Falken-Logo"></div>', unsafe_allow_html=True)
    st.markdown(f"<h2 style='text-align:center; margin-top:0; letter-spacing:0.1em;'>HORST</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center; color:rgba(255,255,255,0.7); margin-top:-0.5rem; font-size:0.85rem;'>Der Falkenhorst des Falken-Wissens</p>", unsafe_allow_html=True)

    st.divider()

    # ── Beispielfragen oben (Hauptzweck) ─────────────────────────────────
    st.subheader("💡 Beispielfragen")
    examples = [
        "Auf welchem Tabellenplatz beendeten die Falken die Saison 2022/23?",
        "Wer war Topscorer der Falken in der Saison 2024/25?",
        "Wer war Trainer der Falken in der Saison 2018/19?",
        "Wer gewann die Halbfinale-Serie zwischen Falken und Hannover Scorpions 2024/25?",
        "Welches Ergebnis hatte das Spiel ECDC Memmingen vs Falken am 27.02.2026?",
        "In welcher Saison hatten die Falken die meisten Punkte aller Zeiten?",
        "Wie viele Saisons spielten die Falken in der DEL2?",
        "🌐 Wann hat der jetzige Besitzer der Tenno Sushi Bar bei den Falken gespielt?",
    ]
    for q in examples:
        if st.button(q, key=f"ex_{hash(q)}", use_container_width=True):
            st.session_state["pending_q"] = q
            st.rerun()

    st.divider()
    if st.button("🗑 Verlauf löschen", use_container_width=True):
        st.session_state.history = []
        st.rerun()

    # ── Backend + Diagnose ganz unten ────────────────────────────────────
    st.divider()
    st.subheader("⚙ Backend")
    st.code(
        f"Gerät:      {_device_label(settings.dgx_base_url)}\n"
        f"Chat:       {settings.dgx_chat_model or '(leer)'}\n"
        f"Embeddings: {settings.dgx_embed_model or '(leer)'} ({settings.dgx_embed_dim}d)\n"
        f"Web-Search: {'Tavily ✓' if settings.tavily_api_key else '— (kein Key)'}",
        language="text",
    )
    with st.expander("🔧 Diagnose"):
        st.markdown("**Aus st.secrets/env geladen:**")
        if _SECRETS_LOADED:
            for k, v in sorted(_SECRETS_LOADED.items()):
                st.text(f"  {k} = {v}")
        else:
            st.warning("Keine Secrets geladen! Bitte in Streamlit Cloud → Settings → Secrets eintragen.")
        st.markdown("**Aktive Config:**")
        st.text(f"  DGX_API_KEY: {'✓' if settings.dgx_api_key else '✗'}")
        st.text(f"  SUPABASE_SERVICE_ROLE_KEY: {'✓' if settings.supabase_service_role_key else '✗'}")
        st.text(f"  TAVILY_API_KEY: {'✓' if settings.tavily_api_key else '✗'}")


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(
    f"""<div class="falken-header">
    <img src="{LOGO_URL}" alt="Falken">
    <div class="falken-header-text">
        <h1>Frag <span class="accent">HORST</span></h1>
        <p>Der Falkenhorst des Falken-Wissens · 45+ Jahre Vereinsgeschichte · Saisons · Spiele · Trainer · Spieler · Playoffs · News</p>
    </div>
    </div>""",
    unsafe_allow_html=True,
)

if "history" not in st.session_state:
    st.session_state.history = []

prefilled = st.session_state.pop("pending_q", "")

q = st.chat_input("Frag HORST …")
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
        web_results = result.get("web_results")
        if web_results:
            with st.expander(f"🌐 Web-Quellen ({len(web_results)})"):
                for w in web_results:
                    st.markdown(f"- [{w.get('title','?')}]({w.get('url','#')})")
                    st.caption(w.get("content","")[:200])
        db_findings = result.get("db_findings")
        if db_findings:
            with st.expander(f"🔗 DB-Cross-Lookups ({len(db_findings)})"):
                for f in db_findings:
                    st.markdown(f"**{f.get('person','?')}**: {f.get('db_answer','')[:300]}")

# Neue Frage
if q:
    with st.chat_message("user", avatar="👤"):
        st.markdown(q)
    with st.chat_message("assistant", avatar="🦅"):
        with st.spinner("🦅 HORST durchsucht den Falkenhorst…"):
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
        web_results = result.get("web_results")
        if web_results:
            with st.expander(f"🌐 Web-Quellen ({len(web_results)})"):
                for w in web_results:
                    st.markdown(f"- [{w.get('title','?')}]({w.get('url','#')})")
                    st.caption(w.get("content","")[:200])
        db_findings = result.get("db_findings")
        if db_findings:
            with st.expander(f"🔗 DB-Cross-Lookups ({len(db_findings)})"):
                for f in db_findings:
                    st.markdown(f"**{f.get('person','?')}**: {f.get('db_answer','')[:300]}")
    st.session_state.history.append({"q": q, "result": result, "t_sec": t_sec})
