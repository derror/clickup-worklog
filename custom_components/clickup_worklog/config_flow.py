"""Config flow for ClickUp Worklog integration."""
import logging
from typing import Any, Dict, Optional

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .api import ClickUpApi, ClickUpApiError
from .const import (
    DOMAIN,
    CONF_API_TOKEN,
    CONF_WORKSPACE_ID,
    CONF_USER_ID,
    CONF_SYNC_MONTHS,
    SERVICE_SYNC_TIMESHEET,
)

_LOGGER = logging.getLogger(__name__)

# This is the schema that used for the configuration UI
STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_API_TOKEN): str,
        vol.Required(CONF_WORKSPACE_ID): str,
        vol.Optional(CONF_USER_ID): str,
    }
)


async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect to ClickUp.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    api = ClickUpApi(
        api_token=data[CONF_API_TOKEN],
        workspace_id=data[CONF_WORKSPACE_ID],
        user_id=data.get(CONF_USER_ID),
    )

    try:
        valid = await hass.async_add_executor_job(api.validate_api_token)
        if not valid:
            raise InvalidAuth
    except ClickUpApiError as err:
        raise CannotConnect from err

    # Return info that you want to store in the config entry.
    return {"title": f"ClickUp Worklog ({data[CONF_WORKSPACE_ID]})"}


class ClickUpWorklogConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ClickUp Worklog."""

    VERSION = 1

    async def async_step_user(
        self, user_input: Optional[Dict[str, Any]] = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                # Create a unique ID based on the workspace ID
                await self.async_set_unique_id(user_input[CONF_WORKSPACE_ID])
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return ClickUpWorklogOptionsFlow(config_entry)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class ClickUpWorklogOptionsFlow(config_entries.OptionsFlow):
    """Handle options for the ClickUp Worklog integration."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Handle options flow."""
        if user_input is not None:
            # If the user clicked the button to sync timesheet
            if user_input.get(CONF_SYNC_MONTHS):
                # Call the service to sync timesheet
                months = int(user_input[CONF_SYNC_MONTHS])
                await self.hass.services.async_call(
                    DOMAIN,
                    SERVICE_SYNC_TIMESHEET,
                    {CONF_SYNC_MONTHS: months},
                    blocking=True,
                )
                # Return to the same form with a message
                return self.async_show_form(
                    step_id="init",
                    data_schema=vol.Schema(
                        {
                            vol.Optional(CONF_SYNC_MONTHS, default="3"): vol.In(
                                {"1": "1 month", "3": "3 months", "6": "6 months", "12": "12 months"}
                            ),
                        }
                    ),
                    description_placeholders={"sync_status": "Synchronization started!"}
                )

        # Show the form
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(CONF_SYNC_MONTHS, default="3"): vol.In(
                        {"1": "1 month", "3": "3 months", "6": "6 months", "12": "12 months"}
                    ),
                }
            ),
        )
