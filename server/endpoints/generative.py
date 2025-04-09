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
from ..providers.OpenMeteoAirQualityProvider import AirQualityData
from ..providers.OpenMeteoAirQualityProvider import OpenMeteoAirQualityProvider
from ..providers.OpenMeteoForecastProvider import DailyForecastData
from ..providers.OpenMeteoForecastProvider import ForecastData
from ..providers.OpenMeteoForecastProvider import OpenMeteoForecastProvider
from ..providers.RNSAProvider import PollenData
from ..providers.RNSAProvider import RNSAProvider


def create_generative_endpoints(
  tag: str,
  api: FastAPI,
  controller: Controller,
  forecast: OpenMeteoForecastProvider,
  air_quality: OpenMeteoAirQualityProvider,
  rnsa: RNSAProvider,
) -> None:
  example_response = Controller.Response[ForecastData | AirQualityData | PollenData].model_validate(
    {
      'provider': 'Open-Météo',
      'input': "Quel temps fait à Paris aujourd'hui ?",
      'message': "Il fait 12 degrés Celsius à Paris aujourd'hui, avec une humideur de 37 pour cent et un vent doux à 4,3 kilomètres par heure. Il commence à se lever à 7h13 et se couche à 20h31. C'est un excellent temps pour sortir et profiter du soleil.",
      'data': {
        'temperature': '12.3°C',
        'humidity': '37%',
        'wind_speed': '4.3 km/h',
        'sunrise': '07:13:00',
        'sunset': '20:31:00',
      },
      'location': {
        'type': 'administrative',
        'name': 'Paris',
        'boundingbox': [48.8155755, 48.902156, 2.224122, 2.4697602],
        'lat': 48.8534951,
        'lon': 2.3483915,
        'addresstype': 'city',
        'display_name': 'Paris, Ile-de-France, Metropolitan France, France',
        'address': {
          'country': 'France',
          'country_code': 'fr',
          'region': 'Metropolitan France',
          'state': 'Ile-de-France',
          'city': 'Paris',
        },
      },
    }
  )

  @api.get(
    '/agent/climate',
    tags=[tag],
    responses={
      200: {
        'content': {
          'application/json': {
            'example': example_response,
          },
        },
      },
      400: {
        'description': 'No location found for user input',
        'content': {
          'application/json': {'example': {'detail': 'No location found for user input'}},
        },
      },
      404: {
        'description': 'Unable to identify service for user input',
        'content': {
          'application/json': {'example': {'detail': 'Unable to identify service for user input'}},
        },
      },
    },
  )
  async def generate_weather_info(
    q: str = Query(
      description='The user question to generate a response from.',
      examples=[
        'What is the weather in Paris today?',
        'Quel temps fait-il à Paris ?',
        'What is the air quality in Paris today?',
        "Quelle est l'air qualité à Paris aujourd'hui ?",
        'What is the pollen count in Paris today?',
        "Quel est le niveau de pollens à Paris aujourd'hui ?",
        'Is it sunny in Paris tomorrow?',
        "Est-ce qu'il fera beau à Paris demain ?",
        'How windy is it in Paris right now?',
        'Quelle est la vitesse du vent à Paris en ce moment ?',
        'What time is sunrise in Paris?',
        'À quelle heure va se lever le soleil à Paris ?',
        'À quelle heure va se coucher le soleil à Paris ?',
        'Va-t-il pleuvoir en soirée sur Paris ?',
        'Will it rain in Paris tomorrow?',
        'Va-t-il pleuvoir à Paris demain ?',
      ],
    ),
    timezone: str = Query(
      default='UTC',
      description='The timezone identifier for the location for which the response is generated.',
      examples=['Europe/Paris', 'Africa/Douala', 'Africa/Lagos', 'America/New_York', 'Asia/Tokyo'],
    ),
    context: str | None = Query(
      default=None,
      description='An optional context string that can be used for generating responses.',
      examples=['Current time: 12:34 PM'],
    ),
  ) -> Controller.Response[ForecastData | DailyForecastData | AirQualityData | PollenData]:
    """
    This endpoint generates responses related to weather, air quality, or pollen
    count for a specific location based on user queries. It identifies the requested
    service and location from the query and retrieves relevant data using appropriate
    providers.

    The query should describe the required information, such as weather forecasts,
    air quality, or pollen data, and may include a specific location. If the location
    is not explicitly provided, the system will attempt to infer it from the query.

    The response includes the requested data, such as temperature, humidity, wind
    speed, sunrise and sunset times, or air quality and pollen levels. If the service
    or location cannot be determined, the endpoint returns an error.
    """
    service, location = await controller.service_agent.get_user_input_service(q, timezone=timezone, context=context or '')

    if service:
      location = location or await controller.location_agent.get_user_input_location(q, context=context or '')

      if location:
        provider = None
        data = None
        dateinfo = None

        if service == 'weather' or service == 'air-quality':
          dateinfo = await controller.get_date(q, timezone=timezone, context=context or '')

          if service == 'weather':
            provider = forecast.name

            if dateinfo.period == 'hourly':
              data = await forecast.fetch(lat=location.lat, lon=location.lon, timezone=timezone)
            else:
              data = await forecast.fetch_daily(lat=location.lat, lon=location.lon, dateinfo=dateinfo)
          elif service == 'air-quality':
            provider = air_quality.name
            data = await air_quality.fetch(lat=location.lat, lon=location.lon)
        elif service == 'pollen':
          provider = rnsa.name
          data = await rnsa.fetch_location(location)

          if not data:
            data = 'Response: Unable to fetch pollen data for the specified location.'

        if provider and data:
          return await controller.generate_response(q, provider, location, data, dateinfo)

      raise HTTPException(status_code=400, detail='No location found for user input')
    raise HTTPException(status_code=404, detail='Unable to identify service for user input')
