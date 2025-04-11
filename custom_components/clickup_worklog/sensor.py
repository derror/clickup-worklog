"""Sensor platform for ClickUp Worklog integration."""
import logging
from datetime import timedelta
from typing import Any, Callable, Dict, List, Optional

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .api import ClickUpApi
from .const import (
    CONF_API_TOKEN,
    CONF_WORKSPACE_ID,
    CONF_USER_ID,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    SENSOR_DAILY_WORKED_TIME,
    SENSOR_WEEKLY_WORKED_TIME,
    SENSOR_MONTHLY_WORKED_TIME,
    ATTR_TOTAL_DURATION,
    ATTR_DURATION_HOURS,
    ATTR_DURATION_MINUTES,
    ATTR_ENTRIES_COUNT,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up ClickUp Worklog sensors based on a config entry."""
    api = ClickUpApi(
        api_token=entry.data[CONF_API_TOKEN],
        workspace_id=entry.data[CONF_WORKSPACE_ID],
        user_id=entry.data.get(CONF_USER_ID),
    )

    # Create a data update coordinator
    coordinator = ClickUpWorklogDataUpdateCoordinator(
        hass,
        _LOGGER,
        api=api,
        name=f"{DOMAIN}_{entry.data[CONF_WORKSPACE_ID]}",
        update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
    )

    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # Store the coordinator in hass.data for access by services
    hass.data.setdefault(DOMAIN, {}).setdefault("coordinators", []).append(coordinator)

    # Create sensor entities
    entities = [
        ClickUpWorklogSensor(
            coordinator,
            entry,
            SENSOR_DAILY_WORKED_TIME,
            "Daily Worked Time",
            "mdi:clock-outline",
            "h",
        ),
        ClickUpWorklogSensor(
            coordinator,
            entry,
            SENSOR_WEEKLY_WORKED_TIME,
            "Weekly Worked Time",
            "mdi:calendar-week",
            "h",
        ),
        ClickUpWorklogSensor(
            coordinator,
            entry,
            SENSOR_MONTHLY_WORKED_TIME,
            "Monthly Worked Time",
            "mdi:calendar-month",
            "h",
        ),
    ]

    async_add_entities(entities)


class ClickUpWorklogDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching ClickUp Worklog data."""

    def __init__(
        self,
        hass: HomeAssistant,
        logger: logging.Logger,
        api: ClickUpApi,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            logger,
            name=name,
            update_interval=update_interval,
        )
        self.api = api

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch data from ClickUp API."""
        try:
            _LOGGER.debug("Updating ClickUp Worklog data")
            # Get data for all time periods
            daily_data = await self.hass.async_add_executor_job(
                self.api.get_daily_worked_time
            )
            _LOGGER.debug("Daily data: %s", daily_data)

            weekly_data = await self.hass.async_add_executor_job(
                self.api.get_weekly_worked_time
            )
            _LOGGER.debug("Weekly data: %s", weekly_data)

            monthly_data = await self.hass.async_add_executor_job(
                self.api.get_monthly_worked_time
            )
            _LOGGER.debug("Monthly data: %s", monthly_data)

            return {
                SENSOR_DAILY_WORKED_TIME: daily_data,
                SENSOR_WEEKLY_WORKED_TIME: weekly_data,
                SENSOR_MONTHLY_WORKED_TIME: monthly_data,
            }
        except Exception as err:
            _LOGGER.error("Error fetching ClickUp Worklog data: %s", err)
            # Return empty data instead of raising an exception
            # This prevents the coordinator from stopping updates
            return {
                SENSOR_DAILY_WORKED_TIME: {
                    "total_duration": 0,
                    "duration_hours": 0,
                    "duration_minutes": 0,
                    "entries_count": 0,
                },
                SENSOR_WEEKLY_WORKED_TIME: {
                    "total_duration": 0,
                    "duration_hours": 0,
                    "duration_minutes": 0,
                    "entries_count": 0,
                },
                SENSOR_MONTHLY_WORKED_TIME: {
                    "total_duration": 0,
                    "duration_hours": 0,
                    "duration_minutes": 0,
                    "entries_count": 0,
                },
            }


class ClickUpWorklogSensor(CoordinatorEntity, SensorEntity):
    """Representation of a ClickUp Worklog sensor."""

    _attr_has_entity_name = True
    _attr_available = True

    def __init__(
        self,
        coordinator: ClickUpWorklogDataUpdateCoordinator,
        config_entry: ConfigEntry,
        sensor_type: str,
        name: str,
        icon: str,
        unit_of_measurement: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._config_entry = config_entry
        self._sensor_type = sensor_type
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unit_of_measurement = unit_of_measurement
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_type}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, config_entry.entry_id)},
            "name": f"ClickUp Worklog ({config_entry.data[CONF_WORKSPACE_ID]})",
            "manufacturer": "ClickUp",
            "model": "Worklog",
        }
        _LOGGER.debug("Created sensor: %s with unique_id: %s", name, self._attr_unique_id)

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data and self._sensor_type in self.coordinator.data:
            data = self.coordinator.data[self._sensor_type]
            # Return hours as a decimal value (e.g., 8.5 for 8 hours and 30 minutes)
            hours = data.get(ATTR_DURATION_HOURS, 0)
            minutes = data.get(ATTR_DURATION_MINUTES, 0)
            return round(hours + (minutes / 60), 2)
        return 0

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data and self._sensor_type in self.coordinator.data:
            data = self.coordinator.data[self._sensor_type]
            return {
                ATTR_TOTAL_DURATION: data.get(ATTR_TOTAL_DURATION, 0),
                ATTR_DURATION_HOURS: data.get(ATTR_DURATION_HOURS, 0),
                ATTR_DURATION_MINUTES: data.get(ATTR_DURATION_MINUTES, 0),
                ATTR_ENTRIES_COUNT: data.get(ATTR_ENTRIES_COUNT, 0),
            }
        return {}
