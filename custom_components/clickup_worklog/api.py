"""API client for ClickUp."""
import logging
import time
from typing import Dict, List, Optional, Any

import requests

from .const import (
    API_BASE_URL,
    API_TIME_ENTRIES_ENDPOINT,
)

_LOGGER = logging.getLogger(__name__)


class ClickUpApiError(Exception):
    """Exception to indicate a ClickUp API error."""


class ClickUpApi:
    """API client for ClickUp."""

    def __init__(self, api_token: str, workspace_id: str, user_id: Optional[str] = None):
        """Initialize the API client."""
        self.api_token = api_token
        self.workspace_id = workspace_id
        self.user_id = user_id
        self.headers = {
            "Authorization": api_token,
            "Content-Type": "application/json",
        }

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make a request to the ClickUp API."""
        url = f"{API_BASE_URL}{endpoint}"

        _LOGGER.debug("Making request to ClickUp API: %s %s with params %s", method, url, params)

        try:
            response = requests.request(
                method,
                url,
                headers=self.headers,
                params=params,
            )

            _LOGGER.debug("ClickUp API response status: %s", response.status_code)

            response.raise_for_status()
            data = response.json()
            _LOGGER.debug("ClickUp API response data: %s", data)
            return data
        except requests.exceptions.RequestException as err:
            _LOGGER.error("Error communicating with ClickUp API: %s", err)
            _LOGGER.error("Response content: %s", getattr(getattr(err, 'response', None), 'text', 'No response content'))
            raise ClickUpApiError(f"Error communicating with ClickUp API: {err}")

    def get_time_entries(self, start_date: int, end_date: int) -> List[Dict]:
        """Get time entries within a date range."""
        endpoint = API_TIME_ENTRIES_ENDPOINT.format(workspace_id=self.workspace_id)

        params = {
            "start_date": start_date,
            "end_date": end_date,
        }

        # If user_id is specified, add it to the params
        if self.user_id:
            params["assignee"] = self.user_id

        _LOGGER.debug("Getting time entries from %s to %s", start_date, end_date)
        try:
            response = self._make_request("GET", endpoint, params)

            if "data" not in response:
                _LOGGER.error("Unexpected response from ClickUp API: %s", response)
                return []

            _LOGGER.debug("Got %d time entries", len(response["data"]))
            return response["data"]
        except ClickUpApiError as err:
            _LOGGER.error("Error getting time entries: %s", err)
            return []

    def get_daily_time_entries(self) -> List[Dict]:
        """Get time entries for the current day."""
        now = int(time.time() * 1000)  # Current time in milliseconds
        # Start of the current day (midnight)
        start_of_day = now - ((now % 86400000))  # 86400000 ms = 24 hours

        _LOGGER.debug("Daily time range: %s to %s", start_of_day, now)
        return self.get_time_entries(start_of_day, now)

    def get_weekly_time_entries(self) -> List[Dict]:
        """Get time entries for the current week."""
        now = int(time.time() * 1000)  # Current time in milliseconds
        start_of_week = now - (7 * 86400000)  # 7 days ago

        _LOGGER.debug("Weekly time range: %s to %s", start_of_week, now)
        return self.get_time_entries(start_of_week, now)

    def get_monthly_time_entries(self) -> List[Dict]:
        """Get time entries for the current month."""
        now = int(time.time() * 1000)  # Current time in milliseconds
        start_of_month = now - (30 * 86400000)  # 30 days ago

        _LOGGER.debug("Monthly time range: %s to %s", start_of_month, now)
        return self.get_time_entries(start_of_month, now)

    def calculate_total_duration(self, time_entries: List[Dict]) -> int:
        """Calculate the total duration from time entries in milliseconds."""
        total_duration = 0

        for entry in time_entries:
            # Skip entries with negative duration (currently running)
            if entry.get("duration") and entry.get("duration") > 0:
                total_duration += entry.get("duration")

        return total_duration

    def get_daily_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the current day."""
        entries = self.get_daily_time_entries()
        total_duration = self.calculate_total_duration(entries)

        return {
            "total_duration": total_duration,
            "duration_hours": total_duration // 3600000,  # Convert ms to hours
            "duration_minutes": (total_duration % 3600000) // 60000,  # Convert remainder to minutes
            "entries_count": len(entries),
            "entries": entries,
        }

    def get_weekly_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the current week."""
        entries = self.get_weekly_time_entries()
        total_duration = self.calculate_total_duration(entries)

        return {
            "total_duration": total_duration,
            "duration_hours": total_duration // 3600000,  # Convert ms to hours
            "duration_minutes": (total_duration % 3600000) // 60000,  # Convert remainder to minutes
            "entries_count": len(entries),
            "entries": entries,
        }

    def get_monthly_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the current month."""
        entries = self.get_monthly_time_entries()
        total_duration = self.calculate_total_duration(entries)

        return {
            "total_duration": total_duration,
            "duration_hours": total_duration // 3600000,  # Convert ms to hours
            "duration_minutes": (total_duration % 3600000) // 60000,  # Convert remainder to minutes
            "entries_count": len(entries),
            "entries": entries,
        }

    def validate_api_token(self) -> bool:
        """Validate the API token by making a test request."""
        try:
            # Try to get authorized teams (workspaces)
            response = self._make_request("GET", "/user")
            return "user" in response
        except ClickUpApiError:
            return False
