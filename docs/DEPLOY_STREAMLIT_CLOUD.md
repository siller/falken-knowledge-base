# Deployment auf Streamlit Community Cloud

Ziel: `falken-kb.streamlit.app` (oder ähnlich), passwortgeschützt für dein Team.

## ⚠ Status 24.07.2026: App ist offline — Re-Deploy nötig

`falken-knowledge-base.streamlit.app` liefert Streamlits `not_found`-Seite (HTTP 404),
d.h. die App existiert auf Streamlit Cloud nicht mehr (Community-Cloud entfernt Apps
nach längerer Inaktivität; letzter Push war 19.05.2026).

**Gegenprobe**: eine bekannte öffentliche App (`30days.streamlit.app`) antwortet über
denselben Weg mit HTTP 200 — es liegt also an der App, nicht am Netz.

**Code ist deploy-ready** (lokal verifiziert 24.07.2026: `streamlit run frontend/falken_ui.py`
→ HTTP 200). Es reicht: neu deployen + Secrets aus `.streamlit/secrets.toml.example` befüllen.

### Re-Deploy-Checkliste (5 Min, im Browser)

1. https://share.streamlit.io → mit GitHub-Account (`siller`) anmelden
2. **"New app"** → **"Deploy a public app from GitHub"**
3. Repository `siller/falken-knowledge-base` · Branch `main` · Main file `frontend/falken_ui.py`
4. **Advanced settings** → Python **3.12**
5. App-URL wieder auf `falken-knowledge-base` setzen (dann bleiben alte Links gültig)
6. Deploy → danach **Settings → Secrets** → Inhalt aus `.streamlit/secrets.toml.example`
   mit echten Werten aus der lokalen `.env` einfügen (**DGX-Block, nicht OpenRouter** —
   die Artikel-Embeddings in der DB sind `nomic-embed-text`)
7. Login testen mit dem gesetzten `app_password`
8. **Gegen das Wieder-Einschlafen**: die App schläft nach 7 Tagen Inaktivität und wird
   nach längerer Inaktivität gelöscht → der GitHub-Actions-Sync
   (`.github/workflows/sync.yml`) pingt sie täglich mit an.

### Secrets für den Sync-Job (GitHub, einmalig)

`Repo → Settings → Secrets and variables → Actions → New repository secret`,
Werte aus der lokalen `.env`:

`SUPABASE_URL` · `SUPABASE_SERVICE_ROLE_KEY` · `DGX_BASE_URL` · `DGX_API_KEY` ·
`DGX_CHAT_MODEL` · `DGX_EMBED_MODEL` · `TAVILY_API_KEY` · `HOCKEYDATA_API_KEY`

Danach einmal `Actions → Daten-Sync → Run workflow` auslösen und das Log prüfen —
am Ende steht ein Aktualitäts-Report (letztes Ergebnis, nächstes Spiel, Artikelzahl).

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

# LLM — DGX (Produktiv-Setup; Artikel-Embeddings in der DB sind nomic-embed-text):
DGX_BASE_URL = "https://pgxapi.siller.io/v1"
DGX_API_KEY = "<aus .env>"
DGX_CHAT_MODEL = "gemma"
DGX_CHAT_FALLBACKS = ""
DGX_EMBED_MODEL = "nomic-embed-text"
DGX_EMBED_DIM = 768

# Web-Search (Multi-Hop-Fragen)
TAVILY_API_KEY = "<aus .env>"

# ODER Fallback OpenRouter — dann vorher `python3 scripts/reembed_articles.py`
# laufen lassen, sonst liefert die News-Suche Müll (anderer Vektorraum):
# DGX_BASE_URL = "https://openrouter.ai/api/v1"
# DGX_API_KEY = "<aus .env>"
# DGX_CHAT_MODEL = "deepseek/deepseek-v4-flash"
# DGX_EMBED_MODEL = "text-embedding-3-small"
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
