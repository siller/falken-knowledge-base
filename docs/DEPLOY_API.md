# Frage-Schnittstelle ausrollen (Cloudron auf siller.io)

Die Schnittstelle (`falken_kb/api/`) beantwortet Fragen der Falken-App. Sie wird
**nicht** von Streamlit mitgestartet und läuft als eigene Cloudron-App.

## Warum eine eigene App und kein Host-Dienst

Gemessen am 08.08.2026 auf `94.130.182.51`:

| Weg | Ergebnis |
|---|---|
| Convex-Container → Host (`172.17.0.1`) | Timeout, Exit 28 |
| Convex-Container → anderer Container | Timeout, Exit 28 |
| Host → Host | erreichbar |

Cloudron kapselt jede App gegeneinander und gegen den Host. Ein Dienst neben
Cloudron wäre für den Convex-Container also unerreichbar. Die Schnittstelle
braucht eine eigene Adresse; TLS und Zertifikat kommen dann von Cloudron.

Erreichbar ist sie damit öffentlich — geschützt allein durch das Geheimnis im
Kopf jeder Anfrage. Ohne gesetztes `API_TOKEN` antwortet sie auf **alles** mit
401; ein Fehlstart stellt sie also nicht offen ins Netz.

## Was bereits erledigt ist

- `Dockerfile`, `CloudronManifest.json` und `deploy/start-cloudron.sh` liegen im Repo.
- Das Image wurde auf dem Server gebaut und geprüft: Zustandsprüfung antwortet,
  eine echte Frage lief in **4,7 s** durch, ohne Geheimnis kam **401**.

## Schritt 1: Image in eine Registry (braucht deinen Token)

Cloudron installiert Apps aus einer Registry, nicht aus einem lokal gebauten
Image. Der GitHub-Token auf dem Mac hat nur `repo`-Rechte — zum Hochladen fehlt
`write:packages`.

Erzeuge unter https://github.com/settings/tokens einen Token mit **`write:packages`**
und **`read:packages`**, dann auf dem Server:

```bash
ssh root@94.130.182.51
export CR_PAT=<der-neue-token>
echo "$CR_PAT" | docker login ghcr.io -u siller --password-stdin

cd /tmp && rm -rf horst-build
git clone --depth 1 https://github.com/siller/falken-knowledge-base.git horst-build
cd horst-build
docker build -t ghcr.io/siller/horst-api:1.0.0 .
docker push ghcr.io/siller/horst-api:1.0.0
```

Danach das Paket unter https://github.com/users/siller/packages auf **öffentlich**
stellen — dann braucht Cloudron keine Zugangsdaten zum Herunterladen.

## Schritt 2: Geheimnis erzeugen

```bash
openssl rand -hex 32
```

Diesen Wert brauchst du zweimal: hier als `API_TOKEN` und später in der
Convex-Umgebung. Beide Seiten müssen exakt übereinstimmen.

## Schritt 3: App in Cloudron installieren

In der Cloudron-Oberfläche: **App Store → Custom App → Install from Docker image**

| Feld | Wert |
|---|---|
| Image | `ghcr.io/siller/horst-api:1.0.0` |
| Domain | `horst-api.siller.io` (oder eine andere freie Subdomain) |
| Memory | 1 GB |

Danach unter **Environment Variables** eintragen (Werte aus der lokalen `.env`):

```
API_TOKEN=<das eben erzeugte Geheimnis>
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
```

## Schritt 4: Gegenprobe

```bash
curl -s https://horst-api.siller.io/gesundheit
# {"status":"ok","modell":"gemma"}

curl -s -X POST https://horst-api.siller.io/frage \
  -H 'Content-Type: application/json' \
  -H "X-Falken-Token: $API_TOKEN" \
  -d '{"frage":"Wer war Topscorer der Falken 2024/25?"}'
```

Erwartet: eine Antwort mit `"beantwortet": true` in vier bis sechs Sekunden.
Ohne den Kopfzeilen-Eintrag muss **401** kommen.

**Zeitgrenze prüfen:** Cloudrons nginx bricht standardmäßig nach 60 Sekunden ab.
Die Schnittstelle gibt nach 40 Sekunden selbst auf, das passt. Wird die Grenze
in Cloudron je gesenkt, macht sie aus einer geordneten Absage einen
Verbindungsabbruch.

## Aktualisieren

```bash
cd /tmp/horst-build && git pull
docker build -t ghcr.io/siller/horst-api:1.0.1 .
docker push ghcr.io/siller/horst-api:1.0.1
```

Dann in Cloudron unter der App das Image auf die neue Marke ändern und neu starten.

## Stellschrauben

Alle als Umgebungsvariablen in Cloudron setzbar, Vorgaben in `falken_kb/config.py`:

| Wert | Vorgabe | Bedeutung |
|---|---|---|
| `API_ZEITGRENZE_SEC` | 40 | Harte Grenze je Anfrage. Bewusst unter den 45 s, die die App wartet. |
| `DGX_TIMEOUT_SEC` | 30 | Grenze je Modellaufruf. Ohne diesen Wert wartet die Bibliothek 600 s. |
| `API_SAMMEL_MAX` | 10 | Höchstzahl Fragen je Sammelaufruf. |
| `API_SAMMEL_PARALLEL` | 1 | Gleichzeitigkeit im Sammelaufruf. Nacheinander ist gemessen schneller. |
| `API_SAMMEL_GESAMT_SEC` | 180 | Gesamtgrenze des Sammelaufrufs. Danach kommt zurück, was fertig ist. |
| `WEB_SEARCH_PROVIDER` | auto | `aus` legt die Websuche still, ohne Schlüssel zu entfernen. |

## Wenn es klemmt

| Symptom | Ursache | Abhilfe |
|---|---|---|
| Alles antwortet mit 401 | `API_TOKEN` nicht gesetzt oder abweichend | Umgebungsvariablen in Cloudron prüfen, App neu starten |
| 503 mit DGX-Meldung | Modell-Endpunkt nicht erreichbar | `curl https://pgxapi.siller.io/v1/models` mit Schlüssel |
| 504 nach 40 Sekunden | DGX im Stau | Logs der App in Cloudron ansehen; hält es an, ist die GPU ausgelastet |
| Antworten ohne Websuche | Exa- oder Tavily-Schlüssel fehlt | Umgebungsvariablen prüfen |
| Cloudron meldet die App als ungesund | Gesundheitspfad nicht erreichbar | `healthCheckPath` ist `/gesundheit`, Port 8000 — im Manifest nachsehen |

## Eine Eigenheit, die man kennen sollte

Läuft eine Anfrage in die 40-Sekunden-Grenze, bekommt der Aufrufer sofort sein
504 — der Arbeits-Thread läuft aber weiter, bis die DGX antwortet oder deren
eigene Grenze greift. Python kann einen Thread nicht abbrechen. Gedeckelt ist
das durch `DGX_TIMEOUT_SEC` (30 s) und die Wiederholungen im Modell-Client; im
schlechtesten Fall hängt ein Faden gut anderthalb Minuten nach.

## Für Server ohne Cloudron

`deploy/horst-api.service` enthält eine systemd-Unit für den Fall, dass die
Schnittstelle einmal auf einem Host ohne Cloudron laufen soll. Auf siller.io
ist sie nicht der richtige Weg.
