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

from ollama import Tool

from ..core.assistant import Assistant
from ..core.geo import Geocode
from ..core.geo import Location


class GetLocationTool:
  def __init__(self, assistant: Assistant, logger: logging.Logger):
    self.logger = logger
    self.agent = assistant.create_tools_agent(
      system=(
        'You are a smart assistant designed to extract geographic location from a user request. '
        'Your main goal is to determine the most relevant location needed to fulfill a location-based request, '
        'such as checking the weather, holidays, time zone, or other services. '
        'You must first look for a location explicitly mentioned in the user request. '
      ),
      tools=[
        Tool(
          function=Tool.Function(
            name='handle_context_location',
            description='Handle context location',
            parameters=Tool.Function.Parameters(
              type='object',
              required=['location'],
              properties={
                'location': Tool.Function.Parameters.Property(type='string', description='The relevant location to handle'),
              },
            ),  # type: ignore
          )
        )
      ],
    )

  async def get_user_input_location(self, user_input: str) -> Location | None:
    result = await self.agent.query(input=f'User Request: {user_input}.')

    if result:
      self.logger.debug(f'Extracted location from user input: {result.arguments}')

      if 'location' in result.arguments:
        place: str = result.arguments['location']

        return await Geocode.find(place)

    return None
