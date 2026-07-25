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

from mcp.server.fastmcp import FastMCP
from mcp.types import PromptMessage
from mcp.types import TextContent
from pydantic import Field


def register_mcp_prompts(mcp: FastMCP) -> None:
  def _build_prompt(request: str, steps: list[str]) -> list[PromptMessage]:
    steps_text = '\\n'.join(f'{i + 1}. {step}' for i, step in enumerate(steps))

    return [
      PromptMessage(
        role='user',
        content=TextContent(
          type='text',
          text=(
            f'The user wants: {request}\\n\\n'
            'Please execute this request by following these steps:\\n'
            f'{steps_text}\\n\\n'
            'Always provide a clear, friendly, and natural language response.'
          ),
        ),
      )
    ]

  @mcp.prompt()
  def current_weather(
    location: Annotated[str, Field(description="The location to get current weather for, e.g., 'Paris, France'.")],
  ) -> list[PromptMessage]:
    """Assist the user in getting the current weather conditions for a specific location."""
    return _build_prompt(
      f'Current weather for {location}',
      [
        'Use `search_locations` to find the latitude and longitude for the location.',
        'Call `get_current_weather` using the obtained coordinates.',
        'Provide a summary of the current weather.',
      ],
    )

  @mcp.prompt()
  def today_weather(
    location: Annotated[str, Field(description="The location to get today's weather forecast for.")],
  ) -> list[PromptMessage]:
    """Assist the user in getting today's weather forecast for a specific location."""
    return _build_prompt(
      f"Today's weather for {location}",
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_hourly_forecast` (for the next 24 hours) or `get_daily_forecast` (for today).',
        'Summarize the expected weather for the rest of today.',
      ],
    )

  @mcp.prompt()
  def tonight_weather(
    location: Annotated[str, Field(description="The location to get tonight's weather forecast for.")],
  ) -> list[PromptMessage]:
    """Assist the user in getting tonight's weather forecast."""
    return _build_prompt(
      f"Tonight's weather for {location}",
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_hourly_forecast`.',
        'Summarize the forecast specifically for tonight.',
      ],
    )

  @mcp.prompt()
  def tomorrow_weather(
    location: Annotated[str, Field(description="The location to get tomorrow's weather forecast for.")],
  ) -> list[PromptMessage]:
    """Assist the user in getting tomorrow's weather forecast."""
    return _build_prompt(
      f"Tomorrow's weather for {location}",
      [
        'Use `search_locations` to find coordinates.',
        "Call `get_daily_forecast` to get tomorrow's forecast overview, and `get_hourly_forecast` if detailed timing is needed.",
        "Summarize tomorrow's weather.",
      ],
    )

  @mcp.prompt()
  def weekend_weather(
    location: Annotated[str, Field(description='The location to get the weekend weather forecast for.')],
  ) -> list[PromptMessage]:
    """Assist the user in getting the weekend weather forecast."""
    return _build_prompt(
      f'Weekend weather for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_daily_forecast` with enough days to cover the upcoming weekend.',
        'Summarize the weather for Saturday and Sunday.',
      ],
    )

  @mcp.prompt()
  def weekly_weather(
    location: Annotated[str, Field(description='The location to get a weekly weather forecast for.')],
  ) -> list[PromptMessage]:
    """Assist the user in getting a weekly weather forecast."""
    return _build_prompt(
      f'Weekly weather for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_daily_forecast` for 7 days.',
        'Summarize the weekly weather trends.',
      ],
    )

  @mcp.prompt()
  def hourly_weather(
    location: Annotated[str, Field(description='The location to get an hourly weather forecast for.')],
  ) -> list[PromptMessage]:
    """Assist the user in getting an hourly weather forecast."""
    return _build_prompt(
      f'Hourly weather for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_hourly_forecast`.',
        'Provide a breakdown of the weather hour by hour.',
      ],
    )

  @mcp.prompt()
  def air_quality(
    location: Annotated[str, Field(description='The location to get the air quality (AQI) for.')],
  ) -> list[PromptMessage]:
    """Assist the user in getting the air quality (AQI) for a location."""
    return _build_prompt(
      f'Air quality for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_air_quality`.',
        'Provide a summary of the current air quality and any health recommendations.',
      ],
    )

  @mcp.prompt()
  def uv_index(
    location: Annotated[str, Field(description='The location to get the UV index forecast for.')],
  ) -> list[PromptMessage]:
    """Assist the user in getting the UV index forecast."""
    return _build_prompt(
      f'UV index for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_daily_forecast` to find the maximum UV index.',
        'Advise the user on sun protection based on the UV index.',
      ],
    )

  @mcp.prompt()
  def weather_alerts(
    location: Annotated[str, Field(description='The location to check for active weather alerts.')],
  ) -> list[PromptMessage]:
    """Assist the user in checking for active weather alerts."""
    return _build_prompt(
      f'Weather alerts for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_weather_alerts`.',
        'Summarize any active severe weather alerts.',
      ],
    )

  @mcp.prompt()
  def sun_times(
    location: Annotated[str, Field(description='The location to get sunrise and sunset times for.')],
  ) -> list[PromptMessage]:
    """Assist the user in getting sunrise and sunset times."""
    return _build_prompt(
      f'Sunrise and sunset times for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_sun_times`.',
        'Provide the sunrise and sunset times for today (and optionally the next few days).',
      ],
    )

  @mcp.prompt()
  def weather_summary(
    location: Annotated[str, Field(description='The location to get a comprehensive weather summary for.')],
  ) -> list[PromptMessage]:
    """Assist the user in getting a comprehensive weather summary."""
    return _build_prompt(
      f'Comprehensive weather summary for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_current_weather`, `get_daily_forecast`, and `get_air_quality`.',
        'Synthesize the data into a complete weather summary.',
      ],
    )

  @mcp.prompt()
  def plan_day(
    location: Annotated[str, Field(description='The location to assist the user in planning their day.')],
  ) -> list[PromptMessage]:
    """Assist the user in planning their day around the weather."""
    return _build_prompt(
      f'Day planning assistance for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_hourly_forecast` and `get_daily_forecast`.',
        'Suggest best times for activities and what to wear.',
      ],
    )

  @mcp.prompt()
  def outdoor_activity(
    location: Annotated[str, Field(description='The location to determine if weather is suitable for outdoor activities.')],
  ) -> list[PromptMessage]:
    """Assist the user in determining if weather is suitable for outdoor activities."""
    return _build_prompt(
      f'Outdoor activity check for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_current_weather`, `get_air_quality`, and `get_pollen` (if in Europe).',
        'Evaluate whether conditions are suitable for being outdoors.',
      ],
    )

  @mcp.prompt()
  def current_pollen_conditions(
    location: Annotated[str, Field(description='The location to check current pollen conditions for.')],
  ) -> list[PromptMessage]:
    """Assist the user in checking current pollen conditions."""
    return _build_prompt(
      f'Current pollen conditions for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_pollen`. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.',
        'Summarize the current pollen levels.',
      ],
    )

  @mcp.prompt()
  def pollen_forecast(
      location: Annotated[
          str,
          Field(description="The location to get the pollen forecast for."),
      ],
  ) -> list[PromptMessage]:
      """Assist the user in getting the pollen forecast."""
      return _build_prompt(
          f"Pollen forecast for {location}",
          [
              "Use `search_locations` to find coordinates.",
              "Call `get_pollen_forecast`. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.",
              "Summarize the overall outlook and provide the daily forecast.",
          ],
      )

  @mcp.prompt()
  def pollen_risk_assessment(
    location: Annotated[str, Field(description='The location to assess pollen allergy risks for.')],
  ) -> list[PromptMessage]:
    """Assist the user in assessing pollen allergy risks."""
    return _build_prompt(
      f'Pollen risk assessment for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_pollen`. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.',
        'Assess the allergy risk based on the severity of present pollens.',
      ],
    )

  @mcp.prompt()
  def pollen_health_advice(
    location: Annotated[str, Field(description='The location to get health advice related to current pollen levels.')],
  ) -> list[PromptMessage]:
    """Assist the user in getting health advice related to current pollen levels."""
    return _build_prompt(
      f'Pollen health advice for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_pollen`. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.',
        'Provide health and prevention advice based on the pollen levels.',
      ],
    )

  @mcp.prompt()
  def outdoor_activity_pollen_check(
    location: Annotated[str, Field(description='The location to check if outdoor activities are safe regarding pollen.')],
  ) -> list[PromptMessage]:
    """Assist the user in checking if outdoor activities are safe regarding pollen."""
    return _build_prompt(
      f'Outdoor activity pollen check for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_pollen` and optionally `get_current_weather`.',
        'Advise on whether it is a good idea to do outdoor activities based on pollen data (only available in Europe).',
      ],
    )

  @mcp.prompt()
  def pollen_alert_subscription(
    location: Annotated[str, Field(description='The location to set up pollen alerts for.')],
  ) -> list[PromptMessage]:
    """Assist the user in setting up pollen alerts."""
    return _build_prompt(
      f'Pollen alert setup for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_pollen` to check baseline levels.',
        'Instruct the user on how they can be reminded or alerted (e.g., using a reminder tool if available), noting the 4-day forecast limit in Europe.',
      ],
    )

  @mcp.prompt()
  def explain_pollen_type(
    pollen_type: Annotated[str, Field(description="The pollen type to explain, e.g., 'birch', 'grass'.")],
  ) -> list[PromptMessage]:
    """Assist the user in understanding a specific pollen type."""
    return _build_prompt(
      f'Explanation for pollen type: {pollen_type}',
      [
        'Use your general knowledge to explain the characteristics of the requested pollen type.',
        'Describe its typical season, the plants it comes from, and its common health impacts.',
      ],
    )

  @mcp.prompt()
  def weather_data_source() -> list[PromptMessage]:
    """Provide information about the data source used for weather forecasts and current conditions."""
    return _build_prompt(
      'Information about the weather forecast data source',
      [
        'Explain that Oremi retrieves current weather conditions and forecasts from the Open-Meteo API.',
        'Mention that Open-Meteo combines weather model output from multiple national weather services into a continuous, seamlessly updated timeseries.',
        'Detail that each time a model run is ingested, the forecast data are stitched to the previous run without gaps or discontinuities, so the hourly timeseries always reflects the latest available initialisation.',
        'Explain that for each location, the highest-resolution applicable model is selected automatically.',
      ],
    )

  @mcp.prompt()
  def air_quality_data_source() -> list[PromptMessage]:
    """Provide information about the data source used for air quality information."""
    return _build_prompt(
      'Information about the air quality data source',
      [
        'Explain that air quality metrics (AQI) are retrieved from the Open-Meteo Air Quality API.',
        'Mention that it calculates EAQI (European Air Quality Index) for European locations and USAQI (US Air Quality Index) for US locations.',
        'Briefly list standard pollutants monitored like PM2.5, PM10, ozone, carbon monoxide, nitrogen dioxide, and sulphur dioxide.',
      ],
    )

  @mcp.prompt()
  def pollen_data_source() -> list[PromptMessage]:
    """Provide information about the data source used for pollen levels and forecasts."""
    return _build_prompt(
      'Information about the pollen data source',
      [
        'Explain that pollen allergen data is sourced from the Copernicus Atmosphere Monitoring Service (CAMS) and served via the Open-Meteo Air Quality API.',
        'Clarify that pollen data is specifically available for locations in Europe during the pollen season with a 4-day forecast.',
        'List the supported pollen allergens: alder, birch, grass, mugwort, olive, and ragweed.',
      ],
    )

  @mcp.prompt()
  def geocoding_data_source() -> list[PromptMessage]:
    """Provide information about the data source used for location geocoding and address lookups."""
    return _build_prompt(
      'Information about the geocoding data source',
      [
        'Explain that location search (forward geocoding) and address lookups (reverse geocoding) are powered by Nominatim OpenStreetMap.',
        'Mention that this service handles coordinates mapping, region detection, and address details using open geospatial data.',
      ],
    )

  @mcp.prompt()
  def data_sources_summary() -> list[PromptMessage]:
    """Provide a comprehensive summary of all external data sources powering Oremi Ojọ."""
    return _build_prompt(
      'Summary of all Oremi Ojọ data sources',
      [
        'Provide a complete overview of all the external APIs and data providers powering Oremi Ojọ.',
        (
          'Include Open-Meteo API for weather forecasts, explaining that it combines weather model output '
          'from multiple national weather services into a continuous, seamlessly updated timeseries '
          'by stitching ingested model runs without gaps, automatically selecting the highest-resolution model for each location.'
        ),
        'Include Open-Meteo Air Quality API (with Copernicus Atmosphere Monitoring Service / CAMS) for air quality and pollen forecasts.',
        'Include Nominatim OpenStreetMap for forward/reverse geocoding and location searches.',
      ],
    )
