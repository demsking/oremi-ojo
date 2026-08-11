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

from mcp.server.mcpserver import MCPServer
from pydantic import Field


def register_mcp_prompts(mcp: MCPServer[None]) -> None:
  def _build_prompt(request: str, steps: list[str]) -> str:
    steps_text = '\\n'.join(f'{i + 1}. {step}' for i, step in enumerate(steps))

    return (
      f'The user wants: {request}\\n\\n'
      'Please execute this request by following these steps:\\n'
      f'{steps_text}\\n\\n'
      'Always provide a clear, friendly, and natural language response.'
    )

  @mcp.prompt(
    title='Current Weather',
    name='current_weather',
    description='Assist the user in getting the current weather conditions for a specific location.',
  )
  def current_weather(
    location: Annotated[str, Field(description="The location to get current weather for, e.g., 'Paris, France'.")],
  ) -> str:
    return _build_prompt(
      f'Current weather for {location}',
      [
        'Use `search_locations` to find the latitude and longitude for the location.',
        'Call `get_current_weather` using the obtained coordinates.',
        'Provide a summary of the current weather.',
      ],
    )

  @mcp.prompt(
    title='Today Weather',
    name='today_weather',
    description="Assist the user in getting today's weather forecast for a specific location.",
  )
  def today_weather(
    location: Annotated[str, Field(description="The location to get today's weather forecast for.")],
  ) -> str:
    return _build_prompt(
      f"Today's weather for {location}",
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_hourly_forecast` (for the next 24 hours) or `get_daily_forecast` (for today).',
        'Summarize the expected weather for the rest of today.',
      ],
    )

  @mcp.prompt(
    title='Tonight Weather',
    name='tonight_weather',
    description="Assist the user in getting tonight's weather forecast.",
  )
  def tonight_weather(
    location: Annotated[str, Field(description="The location to get tonight's weather forecast for.")],
  ) -> str:
    return _build_prompt(
      f"Tonight's weather for {location}",
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_hourly_forecast`.',
        'Summarize the forecast specifically for tonight.',
      ],
    )

  @mcp.prompt(
    title='Tomorrow Weather',
    name='tomorrow_weather',
    description="Assist the user in getting tomorrow's weather forecast.",
  )
  def tomorrow_weather(
    location: Annotated[str, Field(description="The location to get tomorrow's weather forecast for.")],
  ) -> str:
    return _build_prompt(
      f"Tomorrow's weather for {location}",
      [
        'Use `search_locations` to find coordinates.',
        "Call `get_daily_forecast` to get tomorrow's forecast overview, and `get_hourly_forecast` if detailed timing is needed.",
        "Summarize tomorrow's weather.",
      ],
    )

  @mcp.prompt(
    title='Weekend Weather',
    name='weekend_weather',
    description='Assist the user in getting the weekend weather forecast.',
  )
  def weekend_weather(
    location: Annotated[str, Field(description='The location to get the weekend weather forecast for.')],
  ) -> str:
    return _build_prompt(
      f'Weekend weather for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_daily_forecast` with enough days to cover the upcoming weekend.',
        'Summarize the weather for Saturday and Sunday.',
      ],
    )

  @mcp.prompt(
    title='Weekly Weather',
    name='weekly_weather',
    description='Assist the user in getting a weekly weather forecast.',
  )
  def weekly_weather(
    location: Annotated[str, Field(description='The location to get a weekly weather forecast for.')],
  ) -> str:
    return _build_prompt(
      f'Weekly weather for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_daily_forecast` for 7 days.',
        'Summarize the weekly weather trends.',
      ],
    )

  @mcp.prompt(
    title='Hourly Weather',
    name='hourly_weather',
    description='Assist the user in getting an hourly weather forecast.',
  )
  def hourly_weather(
    location: Annotated[str, Field(description='The location to get an hourly weather forecast for.')],
  ) -> str:
    return _build_prompt(
      f'Hourly weather for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_hourly_forecast`.',
        'Provide a breakdown of the weather hour by hour.',
      ],
    )

  @mcp.prompt(
    title='Air Quality',
    name='air_quality',
    description='Assist the user in getting the air quality (AQI) for a location.',
  )
  def air_quality(
    location: Annotated[str, Field(description='The location to get the air quality (AQI) for.')],
  ) -> str:
    return _build_prompt(
      f'Air quality for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_air_quality`.',
        'Provide a summary of the current air quality and any health recommendations.',
      ],
    )

  @mcp.prompt(
    title='UV Index',
    name='uv_index',
    description='Assist the user in getting the UV index forecast.',
  )
  def uv_index(
    location: Annotated[str, Field(description='The location to get the UV index forecast for.')],
  ) -> str:
    return _build_prompt(
      f'UV index for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_daily_forecast` to find the maximum UV index.',
        'Advise the user on sun protection based on the UV index.',
      ],
    )

  @mcp.prompt(
    title='Weather Alerts',
    name='weather_alerts',
    description='Assist the user in checking for active weather alerts.',
  )
  def weather_alerts(
    location: Annotated[str, Field(description='The location to check for active weather alerts.')],
  ) -> str:
    return _build_prompt(
      f'Weather alerts for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_weather_alerts`.',
        'Summarize any active severe weather alerts.',
      ],
    )

  @mcp.prompt(
    title='Sun Times',
    name='sun_times',
    description='Assist the user in getting sunrise and sunset times.',
  )
  def sun_times(
    location: Annotated[str, Field(description='The location to get sunrise and sunset times for.')],
  ) -> str:
    return _build_prompt(
      f'Sunrise and sunset times for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_sun_times`.',
        'Provide the sunrise and sunset times for today (and optionally the next few days).',
      ],
    )

  @mcp.prompt(
    title='Plan Day',
    name='plan_day',
    description='Assist the user in planning their day around the weather.',
  )
  def plan_day(
    location: Annotated[str, Field(description='The location to assist the user in planning their day.')],
  ) -> str:
    return _build_prompt(
      f'Day planning assistance for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_hourly_forecast` and `get_daily_forecast`.',
        'Suggest best times for activities and what to wear.',
      ],
    )

  @mcp.prompt(
    title='Outdoor Activity',
    name='outdoor_activity',
    description='Assist the user in determining if weather is suitable for outdoor activities.',
  )
  def outdoor_activity(
    location: Annotated[str, Field(description='The location to determine if weather is suitable for outdoor activities.')],
  ) -> str:
    return _build_prompt(
      f'Outdoor activity check for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_current_weather`, `get_air_quality`, and `get_current_pollen` (if in Europe).',
        'Evaluate whether conditions are suitable for being outdoors.',
      ],
    )

  @mcp.prompt(
    title='Current Pollen Conditions',
    name='current_pollen_conditions',
    description='Assist the user in checking current pollen conditions.',
  )
  def current_pollen_conditions(
    location: Annotated[str, Field(description='The location to check current pollen conditions for.')],
  ) -> str:
    return _build_prompt(
      f'Current pollen conditions for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_current_pollen`. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.',
        'Summarize the current pollen levels.',
      ],
    )

  @mcp.prompt(
    title='Pollen Forecast',
    name='pollen_forecast',
    description='Assist the user in getting the pollen forecast.',
  )
  def pollen_forecast(
    location: Annotated[
      str,
      Field(description='The location to get the pollen forecast for.'),
    ],
  ) -> str:
    return _build_prompt(
      f'Pollen forecast for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_pollen_forecast`. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.',
        'Summarize the overall outlook and provide the daily forecast.',
      ],
    )

  @mcp.prompt(
    title='Pollen Risk Assessment',
    name='pollen_risk_assessment',
    description='Assist the user in assessing pollen allergy risks.',
  )
  def pollen_risk_assessment(
    location: Annotated[str, Field(description='The location to assess pollen allergy risks for.')],
  ) -> str:
    return _build_prompt(
      f'Pollen risk assessment for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_current_pollen`. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.',
        'Assess the allergy risk based on the severity of present pollens.',
      ],
    )

  @mcp.prompt(
    title='Pollen Health Advice',
    name='pollen_health_advice',
    description='Assist the user in getting health advice related to current pollen levels.',
  )
  def pollen_health_advice(
    location: Annotated[str, Field(description='The location to get health advice related to current pollen levels.')],
  ) -> str:
    return _build_prompt(
      f'Pollen health advice for {location}',
      [
        'Use `search_locations` to find coordinates.',
        'Call `get_current_pollen`. Note: Pollen data is only available in Europe during pollen season with 4 days forecast.',
        'Provide health and prevention advice based on the pollen levels.',
      ],
    )

  @mcp.prompt(
    title='Explain Pollen Type',
    name='explain_pollen_type',
    description='Assist the user in understanding a specific pollen type.',
  )
  def explain_pollen_type(
    pollen_type: Annotated[
      str,
      Field(
        description=(
          'The user request containing the pollen type to explain. '
          'Supported types and their synonyms:\\n'
          "- 'alder_pollen' - Alder tree pollen (synonyms: Alnus, alder catkins). "
          'Early spring pollen from deciduous trees. \\n'
          "- 'birch_pollen' - Birch tree pollen (synonyms: Betula, birch catkins). "
          'One of the most common spring allergens. \\n'
          "- 'grass_pollen' - Grass pollen (synonyms: Poaceae, meadow grass, ryegrass, gramin). "
          'Late spring/summer pollen from various grasses. \\n'
          "- 'mugwort_pollen' - Mugwort pollen (synonyms: Artemisia, wild wormwood). "
          'Late summer/autumn weed pollen. \\n'
          "- 'olive_pollen' - Olive tree pollen (synonyms: Olea, olive blossoms). "
          'Spring pollen from cultivated olive trees, common in Mediterranean regions. \\n'
          "- 'ragweed_pollen' - Ragweed pollen (synonyms: Ambrosia, bitterweed). "
          'Late summer/autumn weed pollen, highly allergenic. \\n\\n'
          "Choose the most appropriate type based on user's description."
        )
      ),
    ],
  ) -> str:
    return (
      f'The user wants an explanation for pollen type: {pollen_type}\\n\\n'
      'Describe its typical season, the plants it comes from, its '
      'geographic distribution, and common health impacts (allergy symptoms).'
      'If the user describes symptoms or asks about management, '
      'offer practical, medically-safe advice (avoidance strategies, '
      'when to seek medical help).\n\n'
      'Do not use any tools. This is a knowledge-based question.\n'
      'Always provide a clear, friendly, and natural language response.'
    )

  @mcp.prompt(
    title='Data Sources',
    name='data_sources',
    description='Provide a comprehensive summary of all external data sources powering Oremi Ojọ.',
  )
  def data_sources() -> str:
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
