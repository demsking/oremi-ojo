# Copyright 2024-2026 Sébastien Demanou. All Rights Reserved.
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
            'example': [
              Location.model_validate(
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
              )
            ],
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
  async def extract_locations(
    q: str = Query(
      description='The user question to generate a response from.',
      examples=[
        'What is the weather in Paris today?',
        'Quel temps fait-il à Douala ?',
        'Compare la meteo entre Paris et Lyon',
        'Quel temps fait-il a Marseille et Nice demain ?',
        'What is the air quality in Yaoundé today?',
        "Quelle est l'air qualité à Laos aujourd'hui ?",
        'What is the pollen count in Ouaguadougou today?',
      ],
    ),
    limit: int = Query(
      default=3,
      ge=1,
      le=10,
      description='Maximum number of locations to return.',
      examples=[1, 1, 3, 4, 5],
    ),
  ) -> list[Location]:
    """
    Extract one or more locations from a free-form user query.

    The endpoint analyzes the request text, detects explicit place mentions,
    geocodes them, and returns structured location objects (coordinates,
    display name, and address details). Use the `limit` parameter to control
    how many matches are returned.

    If no location can be inferred from the input, the endpoint returns an error.
    """
    locations = await controller.location_agent.get_user_input_locations(q, limit=limit)

    if locations:
      return locations

    raise HTTPException(status_code=404, detail='No location found for user input')
