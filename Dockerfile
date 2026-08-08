# Frage-Schnittstelle als Cloudron-App.
#
# WHY Cloudron: auf siller.io kapselt Cloudron jede App. Gemessen am 08.08.2026
# erreicht der Convex-Container weder den Host (Timeout) noch einen anderen
# Container. Ein Host-Dienst wäre also unerreichbar — die Schnittstelle braucht
# eine eigene App mit eigener Adresse, TLS kommt von Cloudron.
FROM cloudron/base:5.0.0

WORKDIR /app/code

COPY requirements.txt ./
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

COPY falken_kb/ ./falken_kb/
COPY deploy/start-cloudron.sh ./

RUN chmod +x start-cloudron.sh

# Cloudron erwartet den Dienst auf 8000 und prüft /gesundheit.
EXPOSE 8000

CMD ["/app/code/start-cloudron.sh"]
