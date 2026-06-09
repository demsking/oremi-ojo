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
import asyncio
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

  async def get_user_input_locations(self, user_input: str, limit: int | None = None) -> list[Location]:
    results = await self.agent.query(input=f'User Request: {user_input}.')
    max_locations = limit or 10

    if not results:
      return []

    places: list[str] = []

    for result in results:
      arguments = result.function.arguments
      self.logger.debug(f'Extracted location call from user input: {arguments}')

      place = arguments.get('location') if arguments else None

      if isinstance(place, str) and place.strip():
        places.append(place.strip())

    unique_places = list(dict.fromkeys(places))
    locations: list[Location] = []
    seen: set[tuple[float, float]] = set()

    # Run geocoding for each extracted place in parallel.
    candidate_lists = await asyncio.gather(*(Geocode.search(place, limit=1) for place in unique_places))

    for candidates in candidate_lists:
      for candidate in candidates:
        key = (candidate.lat, candidate.lon)

        if key in seen:
          continue

        seen.add(key)
        locations.append(candidate)

        if len(locations) >= max_locations:
          return locations

    return locations
