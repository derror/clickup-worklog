"""Constants for the ClickUp Worklog integration."""

# Base component constants
DOMAIN = "clickup_worklog"
NAME = "ClickUp Worklog"
VERSION = "0.1.0"

# Configuration and options
CONF_API_TOKEN = "api_token"
CONF_WORKSPACE_ID = "workspace_id"
CONF_USER_ID = "user_id"  # Optional, if not provided will use the authenticated user

# Defaults
DEFAULT_SCAN_INTERVAL = 300  # 5 minutes

# Sensor names
SENSOR_DAILY_WORKED_TIME = "daily_worked_time"
SENSOR_WEEKLY_WORKED_TIME = "weekly_worked_time"
SENSOR_MONTHLY_WORKED_TIME = "monthly_worked_time"

# API endpoints
API_BASE_URL = "https://api.clickup.com/api/v2"
API_TIME_ENTRIES_ENDPOINT = "/team/{workspace_id}/time_entries"

# Time periods in seconds
ONE_DAY = 86400
ONE_WEEK = 604800
ONE_MONTH = 2592000  # 30 days

# Sensor attributes
ATTR_TOTAL_DURATION = "total_duration"
ATTR_DURATION_HOURS = "duration_hours"
ATTR_DURATION_MINUTES = "duration_minutes"
ATTR_ENTRIES_COUNT = "entries_count"
ATTR_START_TIME = "start_time"
ATTR_END_TIME = "end_time"
ATTR_TASKS = "tasks"
