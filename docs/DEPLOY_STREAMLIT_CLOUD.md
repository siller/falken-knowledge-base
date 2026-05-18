# Deployment auf Streamlit Community Cloud

Ziel: `falken-kb.streamlit.app` (oder ähnlich), passwortgeschützt für dein Team.

## Vorbereitung — fertig ✓

- [x] Git-Repo initialisiert (1 Commit, 90 Files, **keine Secrets im Repo**)
- [x] `requirements.txt` mit allen Dependencies
- [x] `.streamlit/secrets.toml.example` als Vorlage
- [x] `.streamlit/config.toml` für Theme
- [x] UI mit **Password-Auth-Wrapper** (`APP_PASSWORD` env oder `[app_password]` secret)
- [x] UI liest Secrets aus `st.secrets` ODER Env-Vars (lokales `.env` funktioniert weiter)

## Schritt 1: GitHub-Repo erstellen

1. Auf https://github.com/new ein neues Repo erstellen (privat empfohlen) — z.B. `falken-knowledge-base`
2. Im Terminal:
   ```bash
   cd /Users/marksiller/Dropbox/1Privat/_SSO_KI_/FalkenDaten/_Code_/falken-knowledge-base
   git remote add origin https://github.com/DEIN_USER/falken-knowledge-base.git
   git push -u origin main
   ```

## Schritt 2: Streamlit Cloud verbinden

1. Auf https://share.streamlit.io anmelden (mit GitHub-Account)
2. **"New app"** klicken
3. Repository wählen: `DEIN_USER/falken-knowledge-base`
4. Branch: `main`
5. **Main file path**: `frontend/falken_ui.py`
6. **App URL** (optional anpassen): `falken-kb.streamlit.app`
7. Vor dem Deploy → **"Advanced settings"** → **Python version: 3.12**

## Schritt 3: Secrets eintragen

Im Streamlit-Cloud-Dashboard → **App → Settings → Secrets** → diesen Inhalt einfügen
(echte Werte aus deiner lokalen `.env` + APP_PASSWORD):

```toml
# Shared-Password fürs UI (Team-Login)
app_password = "WUNSCH_PASSWORT_HIER"

# Supabase
SUPABASE_URL = "https://supabase.siller.io"
SUPABASE_SERVICE_ROLE_KEY = "<aus .env>"
DATABASE_URL = "postgresql://supabase_admin:<aus .env>@supabase.siller.io:6543/postgres"

# LLM — OpenRouter (Default, RAG-kompatibel zu existing embeddings):
DGX_BASE_URL = "https://openrouter.ai/api/v1"
DGX_API_KEY = "<aus .env>"
DGX_CHAT_MODEL = "deepseek/deepseek-v4-flash"
DGX_CHAT_FALLBACKS = "deepseek/deepseek-chat"
DGX_EMBED_MODEL = "text-embedding-3-small"
DGX_EMBED_DIM = 768

# ODER (für DGX-Backend statt OpenRouter — RAG geht dann NICHT, weil andere Embeddings):
# DGX_BASE_URL = "https://pgxapi.siller.io/v1"
# DGX_API_KEY = "sk-AboUkuaAghVTt_vnPIDqoQ"
# DGX_CHAT_MODEL = "gemma"
# DGX_CHAT_FALLBACKS = ""
# DGX_EMBED_MODEL = "nomic-embed-text"
# DGX_EMBED_DIM = 768
```

Nach Speichern → automatischer Re-Deploy.

## Schritt 4: Team-Zugriff

- App-URL + `app_password` an die Team-Mitglieder geben
- **Restriktion** (optional): in Streamlit Cloud → Settings → "Sharing" → "Only specified email addresses can view this app" → Whitelist
- Bei vielen Nutzern: Streamlit-Cloud Free-Tier hat 1GB RAM / 1 CPU — sollte für ~5 parallele Nutzer reichen

## Schritt 5: Updates pushen

Future-Code-Änderungen einfach:
```bash
git add -A
git commit -m "..."
git push
```
→ Streamlit Cloud baut automatisch neu (~1-2 Min).

## Lokales Testen mit Auth (vor dem Push)

```bash
cd falken-knowledge-base
APP_PASSWORD=test123 streamlit run frontend/falken_ui.py
```

→ http://localhost:8501 → erstmal Login-Screen mit "test123".

## Caveats

1. **Streamlit Free-Tier**: App schläft nach 7 Tagen Inaktivität (1× pro Woche besuchen reicht). Wake-up dauert ~30s.
2. **Memory**: bei langen Sessions kann der Verlauf das 1GB-Limit sprengen — UI hat "Verlauf löschen"-Button.
3. **DGX-Modus**: wenn du auf DGX-Gemma umstellst, verlieren die 10 News-Artikel ihre RAG-Suche (Embeddings-Vektorraum-Mismatch). News würden müssen nochmal mit nomic-embed-text re-embedded werden.
4. **Supabase-Service-Role-Key in Streamlit-Secrets**: hat Vollzugriff auf DB. App ist passwortgeschützt, aber falls der Key leakt = total exposure. Alternative: einen `anon_key` + explizite RLS-Policies (mehr Arbeit, sicherer).

## Alternative: Cloudron später

Wenn du doch auf Cloudron willst, ist die Konvertierung minimal:
- Dockerfile mit `pip install -r requirements.txt && streamlit run frontend/falken_ui.py`
- Cloudron-Manifest mit env-Variablen-Mapping
- Subdomain auf siller.io
