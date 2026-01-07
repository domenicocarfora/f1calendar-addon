"""Constants for the Formula 1 Calendar integration."""
from __future__ import annotations

DOMAIN = "f1calendar"
API_URL = "https://api.jolpi.ca/ergast/f1/current.json"
DEFAULT_UPDATE_INTERVAL = 3600  # 1 ora
MIN_UPDATE_INTERVAL = 300  # 5 minuti
MAX_UPDATE_INTERVAL = 86400  # 24 ore

