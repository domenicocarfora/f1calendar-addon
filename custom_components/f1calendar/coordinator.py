"""DataUpdateCoordinator for Formula 1 Calendar."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Optional, Tuple

import requests
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_URL, DEFAULT_UPDATE_INTERVAL, DOMAIN
from homeassistant.const import CONF_SCAN_INTERVAL

if TYPE_CHECKING:
    from .sensor import F1CalendarSensor

_LOGGER = logging.getLogger(__name__)

try:
    from zoneinfo import ZoneInfo
    ROME_TZ = ZoneInfo("Europe/Rome")
except ImportError:
    try:
        import pytz
        ROME_TZ = pytz.timezone("Europe/Rome")
    except ImportError:
        _LOGGER.warning("Nessun modulo per fusi orari trovato, uso UTC")
        ROME_TZ = None


class F1CalendarCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Formula 1 data."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
    ) -> None:
        """Initialize."""
        self.entry = entry
        update_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_UPDATE_INTERVAL)
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from API."""
        try:
            return await self.hass.async_add_executor_job(self._fetch_data)
        except Exception as err:
            raise UpdateFailed(f"Error communicating with API: {err}") from err

    def _fetch_data(self) -> dict:
        """Fetch data from the API."""
        headers = {"Accept": "application/json"}
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Elabora i dati
        previous_race, current_race, next_race = self._process_f1_data(data)
        
        return {
            "previous_race": previous_race,
            "current_race": current_race,
            "next_race": next_race,
            "raw_data": data,
        }

    def _parse_session_time(self, session_data: dict) -> Tuple[Optional[str], Optional[str]]:
        """Converte la data/ora della sessione nel fuso orario di Roma."""
        if "date" in session_data and "time" in session_data:
            dt_str = f"{session_data['date']}T{session_data['time']}"
            try:
                if dt_str.endswith("Z"):
                    dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                else:
                    dt = datetime.fromisoformat(dt_str)
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=timezone.utc)
                
                if ROME_TZ:
                    dt_rome = dt.astimezone(ROME_TZ)
                    iso_format = dt_rome.isoformat()
                    formatted = dt_rome.strftime("%d/%m/%Y %H:%M")
                    return iso_format, formatted
                else:
                    iso_format = dt.isoformat()
                    formatted = dt.strftime("%d/%m/%Y %H:%M UTC")
                    return iso_format, formatted
            except Exception as e:
                _LOGGER.error(f"Errore nel parsing della data/ora '{dt_str}': {e}")
                return dt_str, None
        elif "date" in session_data:
            return session_data["date"], None
        return None, None

    def _process_f1_data(self, data: dict) -> Tuple[Optional[dict], Optional[dict], Optional[dict]]:
        """Elabora i dati F1 e restituisce gara precedente, attuale e successiva."""
        if not data or "MRData" not in data:
            return None, None, None
        
        races = data["MRData"].get("RaceTable", {}).get("Races", [])
        if not races:
            return None, None, None
        
        now = datetime.now(timezone.utc)
        previous_race = None
        current_race = None
        next_race = None
        
        sorted_races = sorted(races, key=lambda x: x.get("date", ""))
        
        # Trova la gara precedente
        for race in reversed(sorted_races):
            race_date = race.get("date", "")
            race_time = race.get("time", "")
            try:
                if race_time:
                    dt_str = f"{race_date}T{race_time}"
                    race_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                else:
                    race_dt = datetime.fromisoformat(race_date)
                
                if race_dt.tzinfo is None:
                    race_dt = race_dt.replace(tzinfo=timezone.utc)
                
                if race_dt < now:
                    previous_race = race
                    break
            except:
                continue
        
        # Trova la gara corrente
        for race in sorted_races:
            race_date = race.get("date", "")
            race_time = race.get("time", "")
            try:
                if race_time:
                    dt_str = f"{race_date}T{race_time}"
                    race_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                else:
                    race_dt = datetime.fromisoformat(race_date)
                
                if race_dt.tzinfo is None:
                    race_dt = race_dt.replace(tzinfo=timezone.utc)
                
                if race_dt >= now:
                    current_race = race
                    break
            except:
                continue
        
        # Trova la gara successiva
        if current_race:
            current_date = current_race.get("date", "")
            for race in sorted_races:
                if race.get("date", "") > current_date:
                    next_race = race
                    break
        
        return previous_race, current_race, next_race

    def _determine_race_status(self, race_date: str, race_time: Optional[str] = None) -> str:
        """Determina se una gara è passata, attuale o futura."""
        now = datetime.now(timezone.utc)
        
        try:
            if race_time:
                dt_str = f"{race_date}T{race_time}"
                race_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            else:
                race_dt = datetime.fromisoformat(race_date)
            
            if race_dt.tzinfo is None:
                race_dt = race_dt.replace(tzinfo=timezone.utc)
            
            if race_dt < now:
                time_diff = now - race_dt
                if time_diff.days > 7:
                    return "completed"
                else:
                    return "completed"
            else:
                time_diff = race_dt - now
                if time_diff.days <= 7:
                    return "current"
                else:
                    return "upcoming"
        except Exception as e:
            _LOGGER.error(f"Errore nel determinare lo stato della gara: {e}")
            return "unknown"

