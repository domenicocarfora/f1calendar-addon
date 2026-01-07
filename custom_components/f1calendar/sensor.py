"""Sensor platform for Formula 1 Calendar."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.typing import StateType

from .const import DOMAIN
from .coordinator import F1CalendarCoordinator

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="previous_race",
        name="F1 Previous Race",
        icon="mdi:flag-checkered",
    ),
    SensorEntityDescription(
        key="current_race",
        name="F1 Current Race",
        icon="mdi:racing-helmet",
    ),
    SensorEntityDescription(
        key="next_race",
        name="F1 Next Race",
        icon="mdi:flag",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Formula 1 Calendar sensors from a config entry."""
    import logging
    _LOGGER = logging.getLogger(__name__)
    
    if DOMAIN not in hass.data or entry.entry_id not in hass.data[DOMAIN]:
        _LOGGER.error("Coordinator not found in hass.data")
        return
        
    coordinator: F1CalendarCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        F1CalendarSensor(coordinator, description) for description in SENSOR_TYPES
    ]
    
    _LOGGER.info(f"Creating {len(entities)} F1 Calendar sensors: {[e.entity_description.key for e in entities]}")
    async_add_entities(entities, update_before_add=False)


class F1CalendarSensor(CoordinatorEntity[F1CalendarCoordinator], SensorEntity):
    """Representation of a Formula 1 Calendar sensor."""

    def __init__(
        self,
        coordinator: F1CalendarCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = False

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if not self.coordinator.data:
            return "Unavailable"
        
        race_data = self.coordinator.data.get(self.entity_description.key)
        if race_data:
            return race_data.get("raceName", "Unknown")
        return "No data"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the state attributes."""
        if not self.coordinator.data:
            return {}
            
        race_data = self.coordinator.data.get(self.entity_description.key)
        if not race_data:
            return {}

        attributes = {
            "circuit_name": race_data.get("Circuit", {}).get("circuitName", ""),
            "country": race_data.get("Circuit", {}).get("Location", {}).get("country", ""),
            "locality": race_data.get("Circuit", {}).get("Location", {}).get("locality", ""),
            "season": race_data.get("season", ""),
            "round": race_data.get("round", ""),
            "race_date": race_data.get("date", ""),
            "race_type": self.entity_description.key,
        }

        # Processa gli attributi con parsing degli orari
        race = race_data
        coordinator = self.coordinator

        # Aggiungi informazioni sulle sessioni
        if "FirstPractice" in race:
            fp1_iso, fp1_formatted = coordinator._parse_session_time(race["FirstPractice"])
            attributes["first_practice"] = fp1_iso
            attributes["first_practice_formatted"] = fp1_formatted

        if "SecondPractice" in race:
            fp2_iso, fp2_formatted = coordinator._parse_session_time(race["SecondPractice"])
            attributes["second_practice"] = fp2_iso
            attributes["second_practice_formatted"] = fp2_formatted

        if "ThirdPractice" in race:
            fp3_iso, fp3_formatted = coordinator._parse_session_time(race["ThirdPractice"])
            attributes["third_practice"] = fp3_iso
            attributes["third_practice_formatted"] = fp3_formatted

        if "Qualifying" in race:
            qual_iso, qual_formatted = coordinator._parse_session_time(race["Qualifying"])
            attributes["qualifying"] = qual_iso
            attributes["qualifying_formatted"] = qual_formatted

        if "Sprint" in race:
            sprint_iso, sprint_formatted = coordinator._parse_session_time(race["Sprint"])
            attributes["sprint"] = sprint_iso
            attributes["sprint_formatted"] = sprint_formatted

        if "SprintQualifying" in race:
            sprint_qual_iso, sprint_qual_formatted = coordinator._parse_session_time(
                race["SprintQualifying"]
            )
            attributes["sprint_qualifying"] = sprint_qual_iso
            attributes["sprint_qualifying_formatted"] = sprint_qual_formatted

        race_iso, race_formatted = coordinator._parse_session_time(
            {"date": race.get("date", ""), "time": race.get("time", "")}
        )
        attributes["race_time"] = race_iso
        attributes["race_time_formatted"] = race_formatted

        # Determina lo stato
        race_date = race.get("date", "")
        race_time = race.get("time", "")
        status = coordinator._determine_race_status(race_date, race_time)
        attributes["status"] = status

        return attributes

