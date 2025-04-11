#!/usr/bin/env python3
"""Standalone test script for ClickUp API functionality."""
import argparse
import json
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
_LOGGER = logging.getLogger(__name__)

# Constants
API_BASE_URL = "https://api.clickup.com/api/v2"
API_TIME_ENTRIES_ENDPOINT = "/team/{workspace_id}/time_entries"


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
        import requests
        
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
        }

    def validate_api_token(self) -> bool:
        """Validate the API token by making a test request."""
        try:
            # Try to get authorized teams (workspaces)
            response = self._make_request("GET", "/user")
            return "user" in response
        except ClickUpApiError:
            return False


def format_duration(duration_ms):
    """Format a duration in milliseconds to a human-readable string."""
    total_seconds = duration_ms / 1000
    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = int(total_seconds % 60)
    return f"{hours}h {minutes}m {seconds}s"


def test_api(api_token, workspace_id, user_id=None):
    """Test the ClickUp API functionality."""
    _LOGGER.info("Testing ClickUp API functionality...")
    
    # Create the API client
    api = ClickUpApi(api_token, workspace_id, user_id)
    
    # Test API connection
    _LOGGER.info("Testing API connection...")
    try:
        valid = api.validate_api_token()
        if valid:
            _LOGGER.info("✅ API connection successful!")
        else:
            _LOGGER.error("❌ API connection failed: Invalid credentials")
            return False
    except Exception as e:
        _LOGGER.error(f"❌ API connection failed: {e}")
        return False
    
    # Test daily worked time
    _LOGGER.info("\nTesting daily worked time...")
    try:
        daily_data = api.get_daily_worked_time()
        _LOGGER.info(f"Daily worked time: {daily_data.get('duration_hours')}h {daily_data.get('duration_minutes')}m")
        _LOGGER.info(f"Daily entries count: {daily_data.get('entries_count')}")
        
        if daily_data.get('entries_count', 0) > 0:
            _LOGGER.info("✅ Daily worked time calculation successful!")
        else:
            _LOGGER.warning("⚠️ No daily time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Daily worked time calculation failed: {e}")
        return False
    
    # Test weekly worked time
    _LOGGER.info("\nTesting weekly worked time...")
    try:
        weekly_data = api.get_weekly_worked_time()
        _LOGGER.info(f"Weekly worked time: {weekly_data.get('duration_hours')}h {weekly_data.get('duration_minutes')}m")
        _LOGGER.info(f"Weekly entries count: {weekly_data.get('entries_count')}")
        
        if weekly_data.get('entries_count', 0) > 0:
            _LOGGER.info("✅ Weekly worked time calculation successful!")
        else:
            _LOGGER.warning("⚠️ No weekly time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Weekly worked time calculation failed: {e}")
        return False
    
    # Test monthly worked time
    _LOGGER.info("\nTesting monthly worked time...")
    try:
        monthly_data = api.get_monthly_worked_time()
        _LOGGER.info(f"Monthly worked time: {monthly_data.get('duration_hours')}h {monthly_data.get('duration_minutes')}m")
        _LOGGER.info(f"Monthly entries count: {monthly_data.get('entries_count')}")
        
        if monthly_data.get('entries_count', 0) > 0:
            _LOGGER.info("✅ Monthly worked time calculation successful!")
        else:
            _LOGGER.warning("⚠️ No monthly time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Monthly worked time calculation failed: {e}")
        return False
    
    # Test custom period (3 months)
    _LOGGER.info("\nTesting custom period (3 months)...")
    try:
        entries = api.get_custom_period_time_entries(3)
        total_duration = api.calculate_total_duration(entries)
        hours = total_duration // 3600000
        minutes = (total_duration % 3600000) // 60000
        
        _LOGGER.info(f"Custom period (3 months) entries count: {len(entries)}")
        _LOGGER.info(f"Custom period (3 months) total duration: {hours}h {minutes}m")
        
        if len(entries) > 0:
            _LOGGER.info("✅ Custom period calculation successful!")
        else:
            _LOGGER.warning("⚠️ No custom period time entries found")
    except Exception as e:
        _LOGGER.error(f"❌ Custom period calculation failed: {e}")
        return False
    
    _LOGGER.info("\n✅ All tests completed successfully!")
    return True


def main():
    """Run the script."""
    parser = argparse.ArgumentParser(description='Test ClickUp API functionality')
    parser.add_argument('--api-token', required=True, help='ClickUp API token')
    parser.add_argument('--workspace-id', required=True, help='ClickUp workspace ID')
    parser.add_argument('--user-id', help='ClickUp user ID (optional)')
    
    args = parser.parse_args()
    
    test_api(args.api_token, args.workspace_id, args.user_id)


if __name__ == "__main__":
    main()
