# Copyright 2026 Sébastien Demanou. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
from typing import Annotated
from typing import Any

from mcp.server.fastmcp import FastMCP
from pydantic import Field


def register_mcp_prompts(mcp: FastMCP) -> None:
  @mcp.prompt()
  def weather_report(
    location: Annotated[
      str,
      Field(description='The location name or address for which to get the weather report.'),
    ],
    days: Annotated[
      int,
      Field(description='The number of days to include in the forecast (default 3, max 7).'),
    ] = 3,
  ) -> list[dict[str, Any]]:
    """Assist the user in getting a comprehensive weather report for a location."""
    return [
      {
        'role': 'user',
        'content': (
          f'The user wants a weather report for: {location} (forecast duration: {days} days)\n\n'
          'Please follow these steps to fulfill this request:\n'
          '1. Call `search_locations` to find the latitude and longitude for the location.\n'
          '2. If no locations are found, inform the user and ask for clarification.\n'
          '3. Using the coordinates of the first matching location, call the following tools:\n'
          '   - `get_current_weather` to get the current conditions.\n'
          '   - `get_daily_forecast` with the requested number of days.\n'
          '   - `get_weather_alerts` to check for any active weather warnings.\n'
          '4. Present a detailed, beautifully structured weather report including current conditions, daily forecast, and alerts if any.'
        ),
      }
    ]

  @mcp.prompt()
  def outdoor_planner(
    location: Annotated[
      str,
      Field(description='The location name or address to plan the outdoor activity for.'),
    ],
    activity: Annotated[
      str,
      Field(description='The activity name (e.g., running, hiking, biking, picnic, gardening).'),
    ] = 'running',
  ) -> list[dict[str, Any]]:
    """Assist in checking suitability of weather and environment for outdoor activities."""
    return [
      {
        'role': 'user',
        'content': (
          f"The user is planning a/an '{activity}' in '{location}' and wants to know if the weather and environmental conditions are suitable.\n\n"
          'Please follow these steps to help the user:\n'
          '1. Call `search_locations` to find the latitude and longitude for the location.\n'
          '2. If no locations are found, inform the user and ask for clarification.\n'
          '3. Call the following tools using the coordinates:\n'
          '   - `get_current_weather` for current conditions.\n'
          '   - `get_daily_forecast` for the next 3 days.\n'
          '   - `get_air_quality` to check air pollution levels.\n'
          '   - `get_pollen` to check allergen/pollen levels.\n'
          '4. Analyze the conditions (temperature, rain probability, wind, AQI, pollen) and provide a detailed suitability recommendation for the requested activity.'
        ),
      }
    ]

  @mcp.prompt()
  def severe_weather_check(
    location: Annotated[
      str,
      Field(description='The location name or address to check for severe weather warnings.'),
    ],
  ) -> list[dict[str, Any]]:
    """Assist in checking for severe weather warnings and alerts in a location."""
    return [
      {
        'role': 'user',
        'content': (
          f'The user wants to check for severe weather warnings and alerts in: {location}\n\n'
          'Please follow these steps:\n'
          '1. Call `search_locations` to find the coordinates of the location.\n'
          '2. Call `get_weather_alerts` to retrieve any active weather warnings.\n'
          '3. If alerts are found, summarize them clearly, indicating their severity, affected times, and safety recommendations.\n'
          '4. If no alerts are found, inform the user that there are currently no active warnings for that location.'
        ),
      }
    ]
