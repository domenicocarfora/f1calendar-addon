#!/usr/bin/env python3
"""Home Assistant Addon per integrare informazioni Formula 1."""
import os
import sys
import time
import json
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

# Configurazione logging (prima di tutto per poter loggare errori di import)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Gestione del fuso orario di Roma
try:
    from zoneinfo import ZoneInfo
    ROME_TZ = ZoneInfo("Europe/Rome")
    logger.info("Utilizzo zoneinfo per il fuso orario Europe/Rome")
except ImportError:
    # Fallback per versioni Python < 3.9
    try:
        import pytz
        ROME_TZ = pytz.timezone("Europe/Rome")
        logger.info("Utilizzo pytz per il fuso orario Europe/Rome")
    except ImportError:
        logger.warning("Nessun modulo per fusi orari trovato, uso UTC (installare pytz per supporto completo)")
        ROME_TZ = None

# Configurazione
API_URL = "https://api.jolpi.ca/ergast/f1/current.json"
UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", 3600))  # Default 1 ora
HA_URL = os.getenv("HA_URL", "http://supervisor/core")
HA_TOKEN = os.getenv("SUPERVISOR_TOKEN", "")

# Se non c'è il token del supervisor, prova con un token personalizzato
if not HA_TOKEN:
    HA_TOKEN = os.getenv("HA_TOKEN", "")

def get_f1_data() -> Optional[Dict]:
    """Ottiene i dati delle gare F1 dalla API."""
    try:
        headers = {"Accept": "application/json"}
        response = requests.get(API_URL, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Errore nel recupero dati F1: {e}")
        return None

def parse_session_time(session_data: Dict) -> Tuple[Optional[str], Optional[str]]:
    """Converte la data/ora della sessione nel fuso orario di Roma.
    
    Returns:
        Tuple[str, str]: (ISO format, formatted time) o (None, None) se non disponibile
    """
    if "date" in session_data and "time" in session_data:
        dt_str = f"{session_data['date']}T{session_data['time']}"
        try:
            # Parse come UTC (l'API fornisce orari UTC, spesso con Z finale)
            if dt_str.endswith("Z"):
                dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            else:
                dt = datetime.fromisoformat(dt_str)
                # Se non ha timezone, assume UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
            
            # Converti nel fuso orario di Roma
            if ROME_TZ:
                dt_rome = dt.astimezone(ROME_TZ)
                # Formato ISO con offset: YYYY-MM-DDTHH:MM:SS+02:00 (o +01:00)
                iso_format = dt_rome.isoformat()
                # Formato leggibile: "DD/MM/YYYY HH:MM"
                formatted = dt_rome.strftime("%d/%m/%Y %H:%M")
                return iso_format, formatted
            else:
                # Fallback: usa UTC se pytz non è disponibile
                logger.warning("pytz non disponibile, uso UTC invece di Europe/Rome")
                iso_format = dt.isoformat()
                formatted = dt.strftime("%d/%m/%Y %H:%M UTC")
                return iso_format, formatted
        except Exception as e:
            logger.error(f"Errore nel parsing della data/ora '{dt_str}': {e}")
            return dt_str, None
    elif "date" in session_data:
        # Solo data, senza ora
        return session_data["date"], None
    return None, None

def determine_race_status(race_date: str, race_time: Optional[str] = None) -> str:
    """Determina se una gara è passata, attuale o futura."""
    now = datetime.now(timezone.utc)
    
    try:
        if race_time:
            dt_str = f"{race_date}T{race_time}"
            race_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        else:
            # Se non c'è l'ora, assume mezzanotte
            race_dt = datetime.fromisoformat(race_date)
        
        if race_dt.tzinfo is None:
            race_dt = race_dt.replace(tzinfo=timezone.utc)
        
        # Se la gara è già passata (più di qualche ora fa)
        if race_dt < now:
            # Se è passata da più di 7 giorni, è completata
            time_diff = now - race_dt
            if time_diff.days > 7:
                return "completed"
            else:
                # Potrebbe essere ancora considerata "current" se è nel weekend
                return "completed"
        else:
            # Gara futura, controlla se è nel prossimo weekend (entro 7 giorni)
            time_diff = race_dt - now
            if time_diff.days <= 7:
                return "current"
            else:
                return "upcoming"
    except Exception as e:
        logger.error(f"Errore nel determinare lo stato della gara: {e}")
        return "unknown"

def process_f1_data(data: Dict) -> Tuple[Optional[Dict], Optional[Dict], Optional[Dict]]:
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
    
    # Ordina le gare per data
    sorted_races = sorted(races, key=lambda x: x.get("date", ""))
    
    # Trova la gara precedente (ultima completata)
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
    
    # Trova la gara corrente (prossima non ancora completata)
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
    
    # Trova la gara successiva (dopo quella corrente)
    if current_race:
        current_date = current_race.get("date", "")
        for race in sorted_races:
            if race.get("date", "") > current_date:
                next_race = race
                break
    
    return previous_race, current_race, next_race

def create_sensor_state(entity_id: str, state: str, attributes: Dict) -> Dict:
    """Crea lo stato di un sensore per Home Assistant."""
    return {
        "state": state,
        "attributes": attributes
    }

def create_race_attributes(race: Dict, race_type: str) -> Dict:
    """Crea gli attributi per un sensore gara."""
    attributes = {
        "friendly_name": f"F1 {race_type.capitalize()} Race",
        "race_name": race.get("raceName", ""),
        "circuit_name": race.get("Circuit", {}).get("circuitName", ""),
        "country": race.get("Circuit", {}).get("Location", {}).get("country", ""),
        "locality": race.get("Circuit", {}).get("Location", {}).get("locality", ""),
        "season": race.get("season", ""),
        "round": race.get("round", ""),
        "race_date": race.get("date", ""),
        "race_type": race_type,
        "last_updated": datetime.now(ROME_TZ if ROME_TZ else timezone.utc).isoformat()
    }
    
    # Aggiungi informazioni sulle sessioni
    if "FirstPractice" in race:
        fp1_iso, fp1_formatted = parse_session_time(race["FirstPractice"])
        attributes["first_practice"] = fp1_iso
        attributes["first_practice_formatted"] = fp1_formatted
    
    if "SecondPractice" in race:
        fp2_iso, fp2_formatted = parse_session_time(race["SecondPractice"])
        attributes["second_practice"] = fp2_iso
        attributes["second_practice_formatted"] = fp2_formatted
    
    if "ThirdPractice" in race:
        fp3_iso, fp3_formatted = parse_session_time(race["ThirdPractice"])
        attributes["third_practice"] = fp3_iso
        attributes["third_practice_formatted"] = fp3_formatted
    
    if "Qualifying" in race:
        qual_iso, qual_formatted = parse_session_time(race["Qualifying"])
        attributes["qualifying"] = qual_iso
        attributes["qualifying_formatted"] = qual_formatted
    
    if "Sprint" in race:
        sprint_iso, sprint_formatted = parse_session_time(race["Sprint"])
        attributes["sprint"] = sprint_iso
        attributes["sprint_formatted"] = sprint_formatted
    
    if "SprintQualifying" in race:
        sprint_qual_iso, sprint_qual_formatted = parse_session_time(race["SprintQualifying"])
        attributes["sprint_qualifying"] = sprint_qual_iso
        attributes["sprint_qualifying_formatted"] = sprint_qual_formatted
    
    race_iso, race_formatted = parse_session_time({"date": race.get("date", ""), "time": race.get("time", "")})
    attributes["race_time"] = race_iso
    attributes["race_time_formatted"] = race_formatted
    
    # Stato calcolato
    status = determine_race_status(race.get("date", ""), race.get("time", ""))
    attributes["status"] = status
    
    return attributes

def create_sensor_entity_id(race_type: str) -> str:
    """Crea l'entity_id per un sensore."""
    return f"sensor.f1_{race_type}_race"

def update_ha_sensor(entity_id: str, state: str, attributes: Dict) -> bool:
    """Aggiorna un sensore in Home Assistant usando l'API REST."""
    try:
        # Usa il supervisor API per accedere a Home Assistant
        url = f"{HA_URL}/api/states/{entity_id}"
        
        headers = {
            "Authorization": f"Bearer {HA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "state": state,
            "attributes": attributes
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info(f"Sensore {entity_id} aggiornato con successo")
        return True
    except Exception as e:
        logger.error(f"Errore nell'aggiornamento del sensore {entity_id}: {e}")
        # Prova con l'URL diretto del core
        try:
            url = "http://supervisor/core/api/states/" + entity_id
            headers = {
                "Authorization": f"Bearer {HA_TOKEN}",
                "Content-Type": "application/json"
            }
            payload = {
                "state": state,
                "attributes": attributes
            }
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Sensore {entity_id} aggiornato con successo (metodo alternativo)")
            return True
        except Exception as e2:
            logger.error(f"Errore anche con metodo alternativo: {e2}")
            return False

def main():
    """Funzione principale."""
    logger.info("Avvio addon Formula 1 per Home Assistant")
    logger.info(f"Intervallo di aggiornamento: {UPDATE_INTERVAL} secondi")
    
    while True:
        try:
            logger.info("Recupero dati Formula 1...")
            f1_data = get_f1_data()
            
            if not f1_data:
                logger.warning("Nessun dato recuperato, riprovo più tardi")
                time.sleep(UPDATE_INTERVAL)
                continue
            
            previous_race, current_race, next_race = process_f1_data(f1_data)
            
            # Aggiorna sensore gara precedente
            if previous_race:
                entity_id = create_sensor_entity_id("previous")
                attributes = create_race_attributes(previous_race, "previous")
                state = previous_race.get("raceName", "Unknown")
                update_ha_sensor(entity_id, state, attributes)
            else:
                logger.info("Nessuna gara precedente trovata")
            
            # Aggiorna sensore gara attuale
            if current_race:
                entity_id = create_sensor_entity_id("current")
                attributes = create_race_attributes(current_race, "current")
                state = current_race.get("raceName", "Unknown")
                update_ha_sensor(entity_id, state, attributes)
            else:
                logger.info("Nessuna gara attuale trovata")
            
            # Aggiorna sensore gara successiva
            if next_race:
                entity_id = create_sensor_entity_id("next")
                attributes = create_race_attributes(next_race, "next")
                state = next_race.get("raceName", "Unknown")
                update_ha_sensor(entity_id, state, attributes)
            else:
                logger.info("Nessuna gara successiva trovata")
            
            logger.info(f"Aggiornamento completato. Prossimo aggiornamento tra {UPDATE_INTERVAL} secondi")
            
        except KeyboardInterrupt:
            logger.info("Interruzione ricevuta, chiusura addon...")
            break
        except Exception as e:
            logger.error(f"Errore nel loop principale: {e}", exc_info=True)
        
        time.sleep(UPDATE_INTERVAL)

if __name__ == "__main__":
    main()

