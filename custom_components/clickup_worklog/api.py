"""API client for ClickUp."""
import logging
import time
from datetime import datetime, timedelta
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

        _LOGGER.debug("Getting time entries from %s to %s",
                     datetime.fromtimestamp(start_date/1000).strftime('%Y-%m-%d %H:%M:%S'),
                     datetime.fromtimestamp(end_date/1000).strftime('%Y-%m-%d %H:%M:%S'))

        try:
            response = self._make_request("GET", endpoint, params)

            if "data" not in response:
                _LOGGER.error("Unexpected response from ClickUp API: %s", response)
                return []

            entries = response["data"]
            _LOGGER.debug("Got %d time entries", len(entries))

            # Filter out entries with invalid duration
            valid_entries = []
            for entry in entries:
                if "duration" in entry:
                    valid_entries.append(entry)
                else:
                    _LOGGER.warning("Skipping entry without duration: %s", entry.get("id", "unknown"))

            if len(valid_entries) != len(entries):
                _LOGGER.info("Filtered out %d entries with missing duration", len(entries) - len(valid_entries))

            return valid_entries
        except ClickUpApiError as err:
            _LOGGER.error("Error getting time entries: %s", err)
            return []
        except Exception as err:
            _LOGGER.error("Unexpected error getting time entries: %s", err)
            return []

    def get_daily_time_entries(self) -> List[Dict]:
        """Get time entries for the current day."""
        now = int(time.time() * 1000)  # Current time in milliseconds
        # Calculate start of day in user's local timezone
        current_date = datetime.fromtimestamp(now / 1000).date()
        start_of_day = int(datetime.combine(current_date, datetime.min.time()).timestamp() * 1000)

        _LOGGER.debug("Daily time range: %s to %s",
                     datetime.fromtimestamp(start_of_day/1000).strftime('%Y-%m-%d %H:%M:%S'),
                     datetime.fromtimestamp(now/1000).strftime('%Y-%m-%d %H:%M:%S'))
        return self.get_time_entries(start_of_day, now)

    def get_weekly_time_entries(self) -> List[Dict]:
        """Get time entries for the current week."""
        now = int(time.time() * 1000)  # Current time in milliseconds
        # Calculate start of week (7 days ago)
        current_date = datetime.fromtimestamp(now / 1000).date()
        start_of_week = int(datetime.combine(current_date - timedelta(days=7), datetime.min.time()).timestamp() * 1000)

        _LOGGER.debug("Weekly time range: %s to %s",
                     datetime.fromtimestamp(start_of_week/1000).strftime('%Y-%m-%d %H:%M:%S'),
                     datetime.fromtimestamp(now/1000).strftime('%Y-%m-%d %H:%M:%S'))
        return self.get_time_entries(start_of_week, now)

    def get_monthly_time_entries(self) -> List[Dict]:
        """Get time entries for the current month."""
        now = int(time.time() * 1000)  # Current time in milliseconds
        # Calculate start of month (30 days ago)
        current_date = datetime.fromtimestamp(now / 1000).date()
        start_of_month = int(datetime.combine(current_date - timedelta(days=30), datetime.min.time()).timestamp() * 1000)

        _LOGGER.debug("Monthly time range: %s to %s",
                     datetime.fromtimestamp(start_of_month/1000).strftime('%Y-%m-%d %H:%M:%S'),
                     datetime.fromtimestamp(now/1000).strftime('%Y-%m-%d %H:%M:%S'))
        return self.get_time_entries(start_of_month, now)

    def get_custom_period_time_entries(self, months: int) -> List[Dict]:
        """Get time entries for a custom period (in months)."""
        now = int(time.time() * 1000)  # Current time in milliseconds
        # Calculate start date using proper datetime calculation
        current_date = datetime.fromtimestamp(now / 1000).date()
        start_date = int(datetime.combine(current_date - timedelta(days=30 * months), datetime.min.time()).timestamp() * 1000)

        _LOGGER.debug("Custom period time range (%d months): %s to %s",
                     months,
                     datetime.fromtimestamp(start_date/1000).strftime('%Y-%m-%d %H:%M:%S'),
                     datetime.fromtimestamp(now/1000).strftime('%Y-%m-%d %H:%M:%S'))
        return self.get_time_entries(start_date, now)

    def get_current_day_time_entries(self) -> List[Dict]:
        """Get time entries for the current calendar day (today)."""
        now = int(time.time() * 1000)  # Current time in milliseconds
        # Calculate start of current day in user's local timezone
        current_date = datetime.fromtimestamp(now / 1000).date()
        start_of_day = int(datetime.combine(current_date, datetime.min.time()).timestamp() * 1000)

        _LOGGER.debug("Current day time range: %s to %s",
                     datetime.fromtimestamp(start_of_day/1000).strftime('%Y-%m-%d %H:%M:%S'),
                     datetime.fromtimestamp(now/1000).strftime('%Y-%m-%d %H:%M:%S'))
        return self.get_time_entries(start_of_day, now)

    def get_current_week_time_entries(self) -> List[Dict]:
        """Get time entries for the current calendar week (starting Monday)."""
        now = int(time.time() * 1000)  # Current time in milliseconds
        # Calculate start of current week (Monday) in user's local timezone
        current_date = datetime.fromtimestamp(now / 1000).date()
        days_since_monday = current_date.weekday()  # Monday is 0, Sunday is 6
        start_of_week = int(datetime.combine(current_date - timedelta(days=days_since_monday), datetime.min.time()).timestamp() * 1000)

        _LOGGER.debug("Current week time range (from Monday): %s to %s",
                     datetime.fromtimestamp(start_of_week/1000).strftime('%Y-%m-%d %H:%M:%S'),
                     datetime.fromtimestamp(now/1000).strftime('%Y-%m-%d %H:%M:%S'))
        return self.get_time_entries(start_of_week, now)

    def get_current_month_time_entries(self) -> List[Dict]:
        """Get time entries for the current calendar month."""
        now = int(time.time() * 1000)  # Current time in milliseconds
        # Calculate start of current month in user's local timezone
        current_date = datetime.fromtimestamp(now / 1000).date()
        start_of_month = int(datetime.combine(current_date.replace(day=1), datetime.min.time()).timestamp() * 1000)

        _LOGGER.debug("Current month time range: %s to %s",
                     datetime.fromtimestamp(start_of_month/1000).strftime('%Y-%m-%d %H:%M:%S'),
                     datetime.fromtimestamp(now/1000).strftime('%Y-%m-%d %H:%M:%S'))
        return self.get_time_entries(start_of_month, now)

    def calculate_total_duration(self, time_entries: List[Dict]) -> int:
        """Calculate the total duration from time entries in milliseconds."""
        total_duration = 0

        for entry in time_entries:
            # Handle different duration formats
            duration = entry.get('duration')

            # Skip entries with no duration
            if duration is None:
                continue

            # Skip entries with negative duration (currently running)
            if isinstance(duration, (int, float)) and duration > 0:
                total_duration += duration
            # If duration is a string, try to convert it
            elif isinstance(duration, str):
                try:
                    duration_value = int(duration)
                    if duration_value > 0:
                        total_duration += duration_value
                except (ValueError, TypeError):
                    _LOGGER.warning(f"Could not parse duration: {duration}")

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

    def get_current_day_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the current calendar day."""
        entries = self.get_current_day_time_entries()
        total_duration = self.calculate_total_duration(entries)

        return {
            "total_duration": total_duration,
            "duration_hours": total_duration // 3600000,  # Convert ms to hours
            "duration_minutes": (total_duration % 3600000) // 60000,  # Convert remainder to minutes
            "entries_count": len(entries),
            "entries": entries,
        }

    def get_current_week_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the current calendar week (starting Monday)."""
        entries = self.get_current_week_time_entries()
        total_duration = self.calculate_total_duration(entries)

        return {
            "total_duration": total_duration,
            "duration_hours": total_duration // 3600000,  # Convert ms to hours
            "duration_minutes": (total_duration % 3600000) // 60000,  # Convert remainder to minutes
            "entries_count": len(entries),
            "entries": entries,
        }

    def get_current_month_worked_time(self) -> Dict[str, Any]:
        """Get the total worked time for the current calendar month."""
        entries = self.get_current_month_time_entries()
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
