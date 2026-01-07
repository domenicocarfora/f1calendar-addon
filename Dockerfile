ARG BUILD_FROM
FROM ${BUILD_FROM}

# Imposta le label dell'immagine
LABEL \
    io.hass.name="Formula 1 Addon" \
    io.hass.description="Addon per integrare informazioni Formula 1 in Home Assistant" \
    io.hass.type="addon" \
    io.hass.version="1.0.0"

# Installa Python e pip se non già presente
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl

# Crea directory per l'app
RUN mkdir -p /app

# Copia requirements e installa dipendenze
COPY requirements.txt /app/
RUN pip3 install --no-cache-dir -r /app/requirements.txt

# Copia lo script principale
COPY main.py /app/
RUN chmod a+x /app/main.py

# Copia gli script di avvio
COPY run.sh /
RUN chmod a+x /run.sh

# Imposta la directory di lavoro
WORKDIR /app

# Comando di avvio
CMD [ "/run.sh" ]

