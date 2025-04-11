"""The ClickUp Worklog integration."""
import logging
import datetime
import voluptuous as vol
from typing import Any, Dict, List, Optional

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import ClickUpApi
from .const import (
    DOMAIN,
    CONF_API_TOKEN,
    CONF_WORKSPACE_ID,
    CONF_USER_ID,
    CONF_SYNC_MONTHS,
    SERVICE_SYNC_TIMESHEET,
)

_LOGGER = logging.getLogger(__name__)

# List of platforms to support
PLATFORMS = ["sensor"]


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the ClickUp Worklog component from yaml configuration."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ClickUp Worklog from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    # Set up all platforms for this device/entry
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    async def sync_timesheet_service(call: ServiceCall) -> None:
        """Service to sync timesheet data for a specific period."""
        months = call.data.get(CONF_SYNC_MONTHS, 3)
        _LOGGER.info("Syncing timesheet data for the last %d months", months)

        # Get the API client from the first entry (assuming only one entry)
        if not hass.data[DOMAIN]:
            _LOGGER.error("No ClickUp Worklog integration configured")
            return

        entry_id = list(hass.data[DOMAIN].keys())[0]
        entry_data = hass.data[DOMAIN][entry_id]

        api = ClickUpApi(
            api_token=entry_data[CONF_API_TOKEN],
            workspace_id=entry_data[CONF_WORKSPACE_ID],
            user_id=entry_data.get(CONF_USER_ID),
        )

        try:
            # Get time entries for the specified period
            time_entries = await hass.async_add_executor_job(
                api.get_custom_period_time_entries, months
            )

            _LOGGER.info("Synced %d time entries for the last %d months", len(time_entries), months)

            # Force update of all sensors
            for coordinator in hass.data.get(DOMAIN, {}).get("coordinators", []):
                await coordinator.async_refresh()

        except Exception as err:
            _LOGGER.error("Error syncing timesheet data: %s", err)

    # Register the service
    hass.services.async_register(
        DOMAIN,
        SERVICE_SYNC_TIMESHEET,
        sync_timesheet_service,
        schema=vol.Schema({
            vol.Optional(CONF_SYNC_MONTHS, default=3): vol.All(
                vol.Coerce(int), vol.Range(min=1, max=12)
            ),
        }),
    )

    # Reload entry when it's updated
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # Remove config entry from domain
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when it changed."""
    await hass.config_entries.async_reload(entry.entry_id)
