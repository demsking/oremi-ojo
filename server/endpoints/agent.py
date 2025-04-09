# Copyright 2024-2025 Sébastien Demanou. All Rights Reserved.
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
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query

from ..core.controller import Controller
from ..core.geo import Location


def create_agent_endpoints(
  tag: str,
  api: FastAPI,
  controller: Controller,
) -> None:
  @api.get(
    '/agent/location',
    tags=[tag],
    responses={
      200: {
        'content': {
          'application/json': {
            'example': Location.model_validate(
              {
                'type': 'administrative',
                'name': 'Paris',
                'boundingbox': [48.8155755, 48.902156, 2.224122, 2.4697602],
                'lat': 48.8588897,
                'lon': 2.3200410217200766,
                'addresstype': 'suburb',
                'display_name': 'Paris, Ile-de-France, Metropolitan France, France',
                'address': {
                  'country': 'France',
                  'country_code': 'fr',
                  'region': 'Metropolitan France',
                  'state': 'Ile-de-France',
                  'city': 'Paris',
                },
              }
            ),
          },
        },
      },
      404: {
        'description': 'No location found for user input',
        'content': {
          'application/json': {'example': {'detail': 'No location found for user input'}},
        },
      },
    },
  )
  async def extract_location(
    q: str = Query(
      description='The user question to generate a response from.',
      examples=[
        'What is the weather in Paris today?',
        'Quel temps fait-il à Douala ?',
        'What is the air quality in Yaoundé today?',
        "Quelle est l'air qualité à Laos aujourd'hui ?",
        'What is the pollen count in Ouaguadougou today?',
      ],
    ),
    context: str | None = Query(
      default=None,
      description='An optional context string that can be used for generating responses.',
      examples=['Timezone: Africa/Douala'],
    ),
  ) -> Location:
    """
    This endpoint extracts the location from a user query. It analyzes the input
    to identify the geographical location mentioned and returns detailed location
    information, including latitude, longitude, and address components.

    The query may describe a specific location or provide context that helps
    infer the location. If no location can be identified from the input, the
    endpoint returns an error.
    """
    location = await controller.location_agent.get_user_input_location(q, context=context or '')

    if location:
      return location

    raise HTTPException(status_code=404, detail='No location found for user input')
