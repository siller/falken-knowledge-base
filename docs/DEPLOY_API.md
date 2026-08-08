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

## Stand: ausgerollt und geprüft (08.08.2026)

Die Schnittstelle läuft unter **https://horst-api.siller.io** als Cloudron-App
(Kennung `aad6fab5-593b-4ba8-b5b5-888b7e27a158`, Image `localhost:5555/horst-api:1.0.1`).

| Prüfung | Ergebnis |
|---|---|
| Zustandsprüfung über IPv4 | `{"status":"ok","modell":"gemma"}` |
| Zertifikat | Let's Encrypt, gültig bis 06.11.2026 |
| Echte Frage | Topscorer 2024/25 in **5,2 s**, `beantwortet: true` |
| Sammelaufruf, zwei Fragen | 15,4 s, beide beantwortet |
| Ohne Geheimnis | **401** |
| Überlange Frage | **504** — die Absage geht sauber durch Cloudrons nginx, kein Verbindungsabbruch |
| IPv6 | **nicht geprüft** — der Server lauscht auf `[::]:443` und der AAAA-Eintrag löst auf, aber der prüfende Rechner hat kein IPv6 ins Netz |

Der 504-Test lief mit vorübergehend auf 2 Sekunden gesetzter Zeitgrenze; danach
wurde die Vorgabe von 40 Sekunden wiederhergestellt.

### Wie es dorthin kam

- Image liegt in einer Registry **auf dem Server**: `localhost:5555/horst-api:1.0.0`.
  Container `horst-registry`, Port 127.0.0.1:5555, Daten in `/var/lib/horst-registry`.
  Dieser Weg statt ghcr.io, weil der vorhandene GitHub-Token zwar anmelden, aber
  nicht hochladen darf.
- DNS steht bei GoDaddy als A **und** AAAA auf `94.130.182.51` beziehungsweise
  `2a01:4f8:c2c:e66d::1`. Cloudron verwaltet die Zone für `siller.io` nicht selbst.
- Installiert über die Cloudron-API (`POST /api/v1/apps`), Umgebung über
  `POST /api/v1/apps/:id/configure/env`.

### Werte für die Convex-Seite

Adresse und Geheimnis stehen in `deploy/cloudron-env.txt` (nicht im Repo). Der
Convex-Dienst braucht beide:

```
HORST_API_URL=https://horst-api.siller.io
HORST_API_TOKEN=<API_TOKEN aus deploy/cloudron-env.txt>
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
ssh root@94.130.182.51
rm -rf /tmp/horst-build
git clone --depth 1 https://github.com/siller/falken-knowledge-base.git /tmp/horst-build
cd /tmp/horst-build
docker build -t localhost:5555/horst-api:1.0.1 .
docker push localhost:5555/horst-api:1.0.1
```

Dann in Cloudron unter der App das Image auf die neue Marke ändern und neu starten.
Die alte Marke bleibt in der Registry liegen — ein Rücksprung ist damit möglich.

**Achtung beim Update über die API:** `POST /apps/:id/update` stürzt in Cloudron 9.2
ab (`Cannot convert undefined or null to object`, apptask.js:693), wenn das
Manifest der **installierten** App kein `addons`-Feld hat. Das Feld steht seit
Version 1.0.1 im Manifest; Apps, die noch mit dem alten Manifest installiert
wurden, lassen sich nur durch Deinstallieren und Neuinstallieren aktualisieren.
Das ist unkritisch: die App hält keine Daten, alles liegt in Supabase. Die
Umgebungswerte müssen dabei erneut gesetzt werden (`deploy/cloudron-env.txt`).

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
