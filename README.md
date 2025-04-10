# ClickUp Worklog Integration for Home Assistant

This integration allows you to track your ClickUp time entries in Home Assistant. It creates sensors for daily, weekly, and monthly worked time that update every 5 minutes.

## Features

- Daily, weekly, and monthly worked time sensors
- Configurable through the Home Assistant UI
- Updates every 5 minutes
- Displays time in hours with additional attributes for detailed information

## Installation

### Manual Installation

1. Copy the `custom_components/clickup_worklog` directory to your Home Assistant `custom_components` directory
2. Restart Home Assistant
3. Go to Configuration > Integrations
4. Click "Add Integration" and search for "ClickUp Worklog"
5. Follow the configuration steps

### HACS Installation

#### Method 1: Adding as a Custom Repository

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add this repository URL with category "Integration"
5. Click "Install" on the ClickUp Worklog card
6. Restart Home Assistant
7. Go to Configuration > Integrations
8. Click "Add Integration" and search for "ClickUp Worklog"
9. Follow the configuration steps

#### Method 2: If this integration is added to HACS default repositories

1. Open HACS in your Home Assistant instance
2. Go to "Integrations"
3. Search for "ClickUp Worklog"
4. Click "Install"
5. Restart Home Assistant
6. Go to Configuration > Integrations
7. Click "Add Integration" and search for "ClickUp Worklog"
8. Follow the configuration steps

## Configuration

You will need:

1. **ClickUp API Token**: Found in ClickUp settings > Apps
2. **Workspace ID**: Found in the URL when you're in your workspace (e.g., `https://app.clickup.com/{workspace_id}/...`)
3. **User ID** (Optional): If you want to track a specific user's time

## Sensors

The integration creates three sensors:

- `sensor.daily_worked_time`: Shows the total time worked today
- `sensor.weekly_worked_time`: Shows the total time worked this week (last 7 days)
- `sensor.monthly_worked_time`: Shows the total time worked this month (last 30 days)

Each sensor includes the following attributes:

- `total_duration`: Total duration in milliseconds
- `duration_hours`: Hours component of the duration
- `duration_minutes`: Minutes component of the duration
- `entries_count`: Number of time entries in the period

## Troubleshooting

If you encounter issues:

1. Check the Home Assistant logs for errors related to "clickup_worklog"
2. Verify your API token and workspace ID are correct
3. Make sure your ClickUp account has time tracking enabled
4. Ensure you have time entries in the selected time periods

## Support

For issues, feature requests, or contributions, please open an issue on the GitHub repository.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
