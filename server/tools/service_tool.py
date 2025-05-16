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
    name='get_weather',
    description='Handle a forecast request with location information.',
    parameters=Tool.Function.Parameters(
      type='object',
      properties={
        'location': Tool.Function.Parameters.Property(type='string', description='The relevant location to handle'),
      },
    ),  # type: ignore
  )

  handle_air_quality_request = Tool.Function(
    name='get_air_quality',
    description='Handle a air quality request with location information.',
    parameters=handle_forecast_request.parameters,
  )

  handle_pollen_request = Tool.Function(
    name='get_pollen',
    description='Handle a pollen request with location information.',
    parameters=handle_forecast_request.parameters,
  )

  handle_unhandled_request = Tool.Function(
    name='handle_unhandled_request',
    description='Handle a request that cannot be handled by the agent.',
  )

  def __init__(self, assistant: Assistant, logger: logging.Logger):
    self.logger = logger
    self.agent = assistant.create_tools_agent(
      system=(
        "You are a specialized assistant agent designed to identify the requested service—weather, air quality, or pollen—from the user's request. "
        'When possible, extract the relevant location directly from the request or the surrounding context. '
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
    self, user_input: str, *, timezone: str, context: str = ''
  ) -> tuple[Literal['weather', 'air-quality', 'pollen'] | None, Location | None]:
    result = await self.agent.query(input=f'User: {user_input}.\nTimezone: {timezone}.\n{context}')

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
