# Copyright 2025 Sébastien Demanou. All Rights Reserved.
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
from typing import Literal

from ollama import Tool

from ..core.assistant import Assistant
from ..core.geo import Geocode
from ..core.geo import Location


class GetServiceTool:
  handle_forecast_request = Tool.Function(
    name='handle_forecast_request',
    description='Handle a forecast request.',
    parameters=Tool.Function.Parameters(
      type='object',
      required=['location'],
      properties={
        'location': Tool.Function.Parameters.Property(type='string', description='The relevant location to handle'),
      },
    ),
  )

  handle_air_quality_request = Tool.Function(
    name='handle_air_quality_request',
    description='Handle a air quality request.',
    parameters=Tool.Function.Parameters(
      type='object',
      required=['location'],
      properties={
        'location': Tool.Function.Parameters.Property(type='string', description='The relevant location to handle'),
      },
    ),
  )

  handle_pollen_request = Tool.Function(
    name='handle_pollen_request',
    description='Handle a pollen request.',
    parameters=Tool.Function.Parameters(
      type='object',
      required=['location'],
      properties={
        'location': Tool.Function.Parameters.Property(type='string', description='The relevant location to handle'),
      },
    ),
  )

  handle_unhandled_request = Tool.Function(
    name='handle_unhandled_request',
    description='Handle a request that cannot be handled by the agent.',
  )

  def __init__(self, assistant: Assistant, logger: logging.Logger):
    self.logger = logger
    self.agent = assistant.create_tools_agent(
      system=(
        'You are a weather assistant AI specialized in helping users understand local weather, air quality, and pollen forecasts. '
        'You must respond concisely, accurately, and with practical recommendations when applicable. '
        'You have access to specialized tools for handling forecast, air quality, and pollen requests. '
        'Always identify the location involved in the user request. '
        'If the request is vague, ambiguous, or cannot be handled with the available tools, '
        'call the "handle_unhandled_request" function. '
        'Do not invent information. Use tools whenever needed and focus on helping the user make informed decisions based on weather conditions.'
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
    self,
    user_input: str,
    *,
    timezone: str,
  ) -> tuple[Literal['weather', 'air-quality', 'pollen'] | None, Location | None]:
    result = await self.agent.query(input=f'User Request: {user_input}.\nTimezone: {timezone}')

    if result:
      self.logger.debug(f'Extracted service from user input: {result}')

      place = result.arguments.get('location', None)
      location = await Geocode.find(place) if place and result.name != GetServiceTool.handle_unhandled_request.name else None

      if result.name == GetServiceTool.handle_forecast_request.name:
        return 'weather', location

      if result.name == GetServiceTool.handle_air_quality_request.name:
        return 'air-quality', location

      if result.name == GetServiceTool.handle_pollen_request.name:
        return 'pollen', location

    return None, None
