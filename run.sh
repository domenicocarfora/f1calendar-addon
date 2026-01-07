#!/usr/bin/with-contenv bashio

# Carica la configurazione
LOG_LEVEL=$(bashio::config 'log_level')
UPDATE_INTERVAL=$(bashio::config 'update_interval')

# Ottieni il token del supervisor per accedere all'API di HA
SUPERVISOR_TOKEN=$(bashio::supervisor.token)
export SUPERVISOR_TOKEN

# Imposta le variabili d'ambiente
export LOG_LEVEL
export UPDATE_INTERVAL
export HA_URL="http://supervisor/core"

# Log di avvio
bashio::log.info "Starting Formula 1 Addon..."
bashio::log.info "Log level: ${LOG_LEVEL}"
bashio::log.info "Update interval: ${UPDATE_INTERVAL} seconds"

# Avvia l'applicazione Python
exec python3 /app/main.py

