# Frage-Schnittstelle auf siller.io ausrollen

Die Schnittstelle (`falken_kb/api/`) beantwortet Fragen der Falken-App. Sie wird
**nicht** von Streamlit mitgestartet und braucht einen eigenen Dienst neben der DGX.

Aufgerufen wird sie ausschließlich vom Convex-Dienst hinter `falkentipp.siller.io` —
nicht von der App und nicht aus dem offenen Netz.

## Was der Dienst können muss

| Anforderung | Wert |
|---|---|
| Python | 3.11 oder neuer |
| Erreichbar für | den Convex-Dienst, sonst niemanden |
| Antwortzeit | 4–12 s je Frage, harte Grenze bei 40 s |
| Last | eine Frage kostet 2 Modellaufrufe, mit Websuche 3 |

## Schritt 1: Code und Umgebung

```bash
sudo useradd --system --home /opt/horst --shell /usr/sbin/nologin horst
sudo mkdir -p /opt/horst && sudo chown horst:horst /opt/horst

sudo -u horst git clone https://github.com/siller/falken-knowledge-base.git \
    /opt/horst/falken-knowledge-base
cd /opt/horst/falken-knowledge-base
sudo -u horst python3 -m venv .venv
sudo -u horst .venv/bin/pip install -r requirements.txt
```

## Schritt 2: Geheimnisse

Das gemeinsame Geheimnis erzeugen — es muss auf beiden Seiten identisch sein,
hier und in der Convex-Umgebung:

```bash
openssl rand -hex 32
```

Dann `/etc/horst/api.env` anlegen (Rechte streng, die Datei enthält Vollzugriff
auf die Datenbank):

```bash
sudo mkdir -p /etc/horst
sudo tee /etc/horst/api.env >/dev/null <<'ENV'
API_TOKEN=<die-eben-erzeugte-zeichenkette>

SUPABASE_URL=https://supabase.siller.io
SUPABASE_SERVICE_ROLE_KEY=<aus der .env>

DGX_BASE_URL=https://pgxapi.siller.io/v1
DGX_API_KEY=<aus der .env>
DGX_CHAT_MODEL=gemma
DGX_EMBED_MODEL=nomic-embed-text
DGX_EMBED_DIM=768

WEB_SEARCH_PROVIDER=auto
EXA_API_KEY=<aus der .env>
TAVILY_API_KEY=<aus der .env>
ENV
sudo chmod 600 /etc/horst/api.env
sudo chown root:root /etc/horst/api.env
```

**Ohne gesetztes `API_TOKEN` nimmt die Schnittstelle gar keine Fragen an** — sie
antwortet auf alles mit 401. Das ist Absicht: ein Fehlstart soll sie nicht offen
ins Netz stellen.

## Schritt 3: Dienst einrichten

```bash
sudo cp /opt/horst/falken-knowledge-base/deploy/horst-api.service \
        /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now horst-api
systemctl status horst-api --no-pager
```

Prüfen, ob er lebt:

```bash
curl -s http://127.0.0.1:8080/gesundheit
# {"status":"ok","modell":"gemma"}
```

## Schritt 4: Nach außen freigeben

Der Dienst lauscht bewusst nur auf `127.0.0.1`. Nach außen kommt er über den
vorhandenen Reverse-Proxy, zum Beispiel als `horst-api.siller.io`. Wichtig dabei:

- **TLS erzwingen** — das Geheimnis läuft im Kopf jeder Anfrage mit.
- **Zeitgrenze des Proxys auf mindestens 60 Sekunden** setzen. Die Schnittstelle
  gibt nach 40 Sekunden selbst auf; ein Proxy, der früher abbricht, macht aus
  einer geordneten Absage einen Verbindungsabbruch.
- Wenn möglich auf die Adressen des Convex-Dienstes beschränken.

## Schritt 5: Gegenprobe von außen

```bash
curl -s https://horst-api.siller.io/gesundheit

curl -s -X POST https://horst-api.siller.io/frage \
  -H 'Content-Type: application/json' \
  -H "X-Falken-Token: $API_TOKEN" \
  -d '{"frage":"Wer war Topscorer der Falken 2024/25?"}'
```

Erwartet: eine Antwort mit `"beantwortet": true` in vier bis sechs Sekunden.
Ohne den Kopfzeilen-Eintrag muss `401` kommen — wenn nicht, steht das Geheimnis
nicht.

## Betrieb

```bash
journalctl -u horst-api -f              # mitlesen
sudo systemctl restart horst-api        # nach Konfigurationsänderung
```

Aktualisieren:

```bash
cd /opt/horst/falken-knowledge-base
sudo -u horst git pull
sudo -u horst .venv/bin/pip install -r requirements.txt
sudo systemctl restart horst-api
```

## Stellschrauben

Alle über `/etc/horst/api.env` setzbar, Vorgaben in `falken_kb/config.py`:

| Wert | Vorgabe | Bedeutung |
|---|---|---|
| `API_ZEITGRENZE_SEC` | 40 | Harte Grenze je Anfrage. Bewusst unter den 45 s, die die App wartet. |
| `DGX_TIMEOUT_SEC` | 30 | Grenze je Modellaufruf. Ohne diesen Wert wartet die Bibliothek 600 s. |
| `API_SAMMEL_MAX` | 10 | Höchstzahl Fragen je Sammelaufruf. |
| `API_SAMMEL_PARALLEL` | 1 | Gleichzeitigkeit im Sammelaufruf. Nacheinander ist gemessen schneller — siehe Kommentar in der Config. |
| `WEB_SEARCH_PROVIDER` | auto | `aus` legt die Websuche still, ohne Schlüssel zu entfernen. |

## Wenn es klemmt

| Symptom | Ursache | Abhilfe |
|---|---|---|
| Alles antwortet mit 401 | `API_TOKEN` nicht gesetzt oder abweichend | `/etc/horst/api.env` prüfen, Dienst neu starten |
| 503 mit DGX-Meldung | Modell-Endpunkt nicht erreichbar | `curl https://pgxapi.siller.io/v1/models` mit Schlüssel |
| 504 nach 40 Sekunden | DGX im Stau | `journalctl -u horst-api` ansehen; hält es an, ist die GPU ausgelastet |
| Antworten ohne Websuche | Exa- oder Tavily-Schlüssel fehlt | Kasten „Web-Search" in der Umgebungsdatei |
| Dienst startet nicht | Abhängigkeiten fehlen | `.venv/bin/pip install -r requirements.txt` erneut |
