"""Device information for Formula 1 Calendar."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import F1CalendarCoordinator


class F1CalendarEntity(CoordinatorEntity):
    """Base entity for Formula 1 Calendar."""

    def __init__(self, coordinator: F1CalendarCoordinator) -> None:
        """Initialize the base entity."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.entry.entry_id)},
            name="Formula 1 Calendar",
            manufacturer="Ergast API",
            model="F1 Calendar",
        )

