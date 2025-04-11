# ClickUp Worklog Integration Tests

This directory contains test scripts to help diagnose issues with the ClickUp Worklog integration.

## Available Tests

1. **test_clickup_api.py** - Tests the ClickUp API integration, including connection, time entries, and time calculations.
2. **test_api_response.py** - Tests the ClickUp API response structure directly.
3. **debug_time_calculation.py** - Debugs the time calculation logic in detail.

## Running the Tests

### 1. Test ClickUp API Integration

This test verifies the API connection, fetches time entries, and tests time calculations.

```bash
python tests/test_clickup_api.py --api-token YOUR_API_TOKEN --workspace-id YOUR_WORKSPACE_ID [--user-id YOUR_USER_ID]
```

### 2. Test API Response Structure

This test directly calls the ClickUp API and examines the response structure.

```bash
python tests/test_api_response.py --api-token YOUR_API_TOKEN --workspace-id YOUR_WORKSPACE_ID [--start-date START_DATE_MS] [--end-date END_DATE_MS]
```

### 3. Debug Time Calculation

This test debugs the time calculation logic in detail.

```bash
python tests/debug_time_calculation.py --api-token YOUR_API_TOKEN --workspace-id YOUR_WORKSPACE_ID [--user-id YOUR_USER_ID]
```

## Troubleshooting

If the tests reveal issues, here are some common problems and solutions:

1. **API Connection Issues**:
   - Verify your API token is correct and has the necessary permissions
   - Check your internet connection
   - Ensure the workspace ID is correct

2. **Empty Time Entries**:
   - Verify you have time entries in the specified time periods
   - Check if the user ID is correct (if specified)
   - Examine the time ranges being used

3. **Time Calculation Issues**:
   - Check the format of the time entries returned by the API
   - Verify the duration field is present and has the expected format
   - Look for any negative duration values (which might indicate currently running time entries)

## Fixing Common Issues

### 1. Time Range Calculation

If the time ranges are incorrect, check the calculation in the API class:

```python
# Daily time range
start_of_day = now - ((now % 86400000))  # Start of the current day

# Weekly time range
start_of_week = now - (7 * 86400000)  # 7 days ago

# Monthly time range
start_of_month = now - (30 * 86400000)  # 30 days ago
```

### 2. Duration Calculation

If the duration calculation is incorrect, check the `calculate_total_duration` method:

```python
def calculate_total_duration(self, time_entries):
    """Calculate the total duration from time entries in milliseconds."""
    total_duration = 0
    
    for entry in time_entries:
        # Skip entries with negative duration (currently running)
        if entry.get("duration") and entry.get("duration") > 0:
            total_duration += entry.get("duration")
            
    return total_duration
```

### 3. API Response Handling

If the API response is not being handled correctly, check the `get_time_entries` method:

```python
def get_time_entries(self, start_date, end_date):
    """Get time entries within a date range."""
    endpoint = API_TIME_ENTRIES_ENDPOINT.format(workspace_id=self.workspace_id)
    
    params = {
        "start_date": start_date,
        "end_date": end_date,
    }
    
    # If user_id is specified, add it to the params
    if self.user_id:
        params["assignee"] = self.user_id
        
    response = self._make_request("GET", endpoint, params)
    
    if "data" not in response:
        _LOGGER.error("Unexpected response from ClickUp API: %s", response)
        return []
        
    return response["data"]
```
