#!/bin/bash
set -eu

# Cloudron reicht Umgebungsvariablen aus der App-Konfiguration durch. Ohne
# API_TOKEN nimmt die Schnittstelle keine Fragen an — das ist Absicht, siehe
# falken_kb/api/app.py.
if [ -z "${API_TOKEN:-}" ]; then
    echo "WARNUNG: API_TOKEN ist nicht gesetzt — die Schnittstelle weist alles mit 401 ab." >&2
fi

exec /usr/bin/python3 -m uvicorn falken_kb.api.app:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 2 \
    --timeout-keep-alive 65
