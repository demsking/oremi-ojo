# Copyright 2025-2026 Sébastien Demanou. All Rights Reserved.
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
import logging
from typing import Any
from typing import Literal

from ollama import Message
from ollama import Tool

from ..core.geo import Geocode
from ..core.geo import Location
from ..llm.agent import AgentClient

logger = logging.getLogger(__name__)


class GetServiceTool:
  Service = Literal['weather', 'air-quality', 'pollen']

  handle_forecast_request = Tool.Function(
    name='get_weather',
    description='Handle a forecast request with location information and specific weather variables.',
    parameters=Tool.Function.Parameters(
      type='object',
      properties={
        'location': Tool.Function.Parameters.Property(type='string', description='The relevant location to handle'),
        'hourly_variables': Tool.Function.Parameters.Property(
          type='array',
          items=Tool.Function.Parameters.Property(type='string'),
          description='Specific hourly weather variables requested by the user, if any (e.g. temperature_2m, relative_humidity_2m, apparent_temperature, precipitation, wind_speed_10m, weather_code, uv_index, is_day, visibility, pressure_msl). Only specify if explicitly mentioned or strongly implied.',
        ),
        'daily_variables': Tool.Function.Parameters.Property(
          type='array',
          items=Tool.Function.Parameters.Property(type='string'),
          description='Specific daily weather variables requested by the user, if any (e.g. temperature_2m_max, temperature_2m_min, sunrise, sunset, rain_sum, wind_speed_10m_max, uv_index_max). Only specify if explicitly mentioned or strongly implied.',
        ),
      },
    ),  # type: ignore
  )

  handle_air_quality_request = Tool.Function(
    name='get_air_quality',
    description='Handle an air quality request with location information and specific pollutants/variables.',
    parameters=Tool.Function.Parameters(
      type='object',
      properties={
        'location': Tool.Function.Parameters.Property(type='string', description='The relevant location to handle'),
        'variables': Tool.Function.Parameters.Property(
          type='array',
          items=Tool.Function.Parameters.Property(type='string'),
          description='Specific air quality variables or pollutants requested, if any (e.g. pm2_5, pm10, carbon_monoxide, nitrogen_dioxide, sulphur_dioxide, ozone, european_aqi, us_aqi). Only specify if explicitly mentioned or strongly implied.',
        ),
      },
    ),  # type: ignore
  )

  handle_pollen_request = Tool.Function(
    name='get_pollen',
    description='Handle a pollen request with location information.',
    parameters=Tool.Function.Parameters(
      type='object',
      properties={
        'location': Tool.Function.Parameters.Property(type='string', description='The relevant location to handle'),
      },
    ),  # type: ignore
  )

  handle_unhandled_request = Tool.Function(
    name='handle_unhandled_request',
    description='Handle a request that cannot be handled by the agent.',
  )

  def __init__(self, assistant: AgentClient):
    self.agent = assistant.create_tools_agent(
      system=(
        "You are a specialized assistant agent designed to identify the requested service—weather, air quality, or pollen—from the user's request. "
        'When possible, extract the relevant location directly from the request or the surrounding context. '
        'Also extract specific weather/air quality variables if the user explicitly asks about specific parameters (such as temperature, rain, wind, AQI, PM2.5, etc.). '
        'Respond concisely and accurately, providing practical, actionable recommendations when appropriate. '
        'Use the dedicated tools available for forecasts, air quality, and pollen data. '
        'If the service type or location is missing, unclear, or cannot be handled using available tools, '
        f'call the "{GetServiceTool.handle_unhandled_request.name}" function. '
        'Do not invent information. Always rely on tools when needed and aim to help users make informed decisions based on environmental conditions.'
      ),
      tools=[
        Tool(
          function=GetServiceTool.handle_forecast_request,
        ),
        Tool(
          function=GetServiceTool.handle_air_quality_request,
        ),
        Tool(
          function=GetServiceTool.handle_pollen_request,
        ),
        Tool(
          function=GetServiceTool.handle_unhandled_request,
        ),
      ],
    )

  async def get_user_input_service(
    self, result: Message.ToolCall.Function
  ) -> tuple[Service | None, Location | None, dict[str, Any] | None]:
    logger.debug(f'Extracted service from user input: {result}')

    place = result.arguments.get('location', None)
    location = await Geocode.find(place) if place and result.name != GetServiceTool.handle_unhandled_request.name else None

    # Extract dynamic parameters if present
    args = {}
    if 'hourly_variables' in result.arguments:
      args['hourly_variables'] = result.arguments['hourly_variables']

    if 'daily_variables' in result.arguments:
      args['daily_variables'] = result.arguments['daily_variables']

    if 'variables' in result.arguments:
      args['variables'] = result.arguments['variables']

    if result.name == GetServiceTool.handle_forecast_request.name:
      return 'weather', location, args

    if result.name == GetServiceTool.handle_air_quality_request.name:
      return 'air-quality', location, args

    if result.name == GetServiceTool.handle_pollen_request.name:
      return 'pollen', location, args

    return None, None, None

  async def get_user_input_services(
    self, user_input: str, *, timezone: str, context: str = ''
  ) -> list[tuple[Service | None, Location | None, dict[str, Any] | None]]:
    results = await self.agent.query(f'User: {user_input}.\nTimezone: {timezone}.\n{context}')

    if results:
      logger.debug(f'Found {len(results)} tool calls in the response.')

      services: list[tuple[GetServiceTool.Service | None, Location | None, dict[str, Any] | None]] = []

      for tool_call in results:
        service, location, args = await self.get_user_input_service(tool_call.function)

        if service:
          services.append((service, location, args))

      return services

    return []
