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
from types import NoneType
from typing import Any

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query

from ..core.controller import Controller
from ..core.controller import WeatherService
from ..core.time import get_current_datetime
from ..models.air_quality import EAQIData
from ..models.air_quality import USAQIData
from ..providers.MeteoPollenProvider import MeteoPollenProvider
from ..providers.MeteoPollenProvider import PollenData
from ..providers.OpenMeteoAirQualityProvider import AirQualityData
from ..providers.OpenMeteoAirQualityProvider import OpenMeteoAirQualityProvider
from ..providers.OpenMeteoForecastProvider import DailyForecastData
from ..providers.OpenMeteoForecastProvider import ForecastData
from ..providers.OpenMeteoForecastProvider import OpenMeteoForecastProvider
from ..providers.OpenMeteoForecastProvider import TemperatureUnit


def create_generative_endpoints(
  tag: str,
  api: FastAPI,
  controller: Controller,
  forecast: OpenMeteoForecastProvider,
  air_quality: OpenMeteoAirQualityProvider,
  pollen: MeteoPollenProvider,
) -> None:
  example_response = Controller.Response[ForecastData | AirQualityData | PollenData].model_validate(
    {
      'provider': 'Open-Météo',
      'service': 'weather',
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
    temperature_unit: TemperatureUnit = Query(
      'celsius',
      alias='temperature-unit',
      description=(
        'Unit of temperature to use when returning weather data. '
        'This affects how temperature values are formatted in the response.'
      ),
      examples=['celsius', 'fahrenheit'],
    ),
  ) -> Controller.Response[ForecastData | DailyForecastData | USAQIData | EAQIData | PollenData | NoneType]:
    """
    Generates a weather-related response based on the user's natural language
    query. This may include current or forecasted weather, air quality, or
    pollen levels for a specific location.

    The endpoint interprets user questions to determine both the requested
    service (e.g., weather forecast, air quality, or pollen count) and the
    location. If a location is not explicitly mentioned in the query, the
    system attempts to infer it using internal heuristics.

    Depending on the identified service, the appropriate external data provider
    is queried to fetch relevant information. For weather and air quality
    services, the endpoint also parses the query for any time-related
    information such as "today" or "tomorrow" to determine whether to return
    hourly or daily data.

    The response contains detailed environmental data tailored to the user's
    query. If the system fails to determine a valid location or service from
    the input, an appropriate error message is returned.
    """
    service, location = await controller.service_agent.get_user_input_service(q, timezone=timezone)

    if service:
      location = location or await controller.location_agent.get_user_input_location(q)

      if location:
        provider = None
        data = None
        dateinfo = None

        if service == 'weather' or service == 'air-quality':
          dateinfo = await controller.get_date(q, timezone=timezone)

          if service == 'weather':
            provider = forecast.name

            if dateinfo.period == 'hourly':
              data = await forecast.fetch(
                lat=location.lat, lon=location.lon, timezone=timezone, temperature_unit=temperature_unit
              )
            else:
              data = await forecast.fetch_daily(
                lat=location.lat, lon=location.lon, dateinfo=dateinfo, temperature_unit=temperature_unit
              )
          elif service == 'air-quality':
            provider = air_quality.name
            data = await air_quality.fetch(lat=location.lat, lon=location.lon)
        elif service == 'pollen':
          provider = pollen.name
          data = await pollen.fetch(lon=location.lon, lat=location.lat)

        if provider:
          return await controller.generate_response(q, provider, location, service, data, temperature_unit, dateinfo)

      raise HTTPException(status_code=400, detail='No location found for user input')
    raise HTTPException(status_code=404, detail='Unable to identify service for user input')

  @api.get(
    '/agent/alerts',
    tags=[tag],
    responses={
      200: {
        'content': {
          'application/json': {
            'example': Controller.AlertResponse[Any].model_validate(
              {
                'provider': 'Open-Météo',
                'service': 'air-quality',
                'message': "Alert! From Open-Météo, today's air quality is poor with an AQI of 32. Pollen levels are moderate from grass and weeds.\n\nWear comfortable clothing and stay hydrated to cope with the heat.",
                'data': {'value': 28, 'level': 'fair', 'unit': 'EAQI'},
              }
            ),
          },
        },
      },
    },
  )
  async def generate_alerts_info(
    service: WeatherService = Query(
      description='The type of weather-related service for which the alert is requested.',
      examples=['air-quality', 'weather', 'pollen'],
    ),
    lat: float = Query(
      description='The latitude of the location for which the alert is generated.',
      examples=[48.8534951],
    ),
    lon: float = Query(
      description='The longitude of the location for which the alert is generated.',
      examples=[2.3483915],
    ),
    timezone: str = Query(
      default='UTC',
      description='The timezone identifier for the location for which the response is generated.',
      examples=['Europe/Paris', 'Africa/Douala', 'Africa/Lagos', 'America/New_York', 'Asia/Tokyo'],
    ),
    language: str = Query(
      'en',
      description='Language code for the alert message content.',
      examples=['fr', 'en'],
    ),
    temperature_unit: TemperatureUnit = Query(
      'celsius',
      alias='temperature-unit',
      description='Preferred unit for temperature values in alerts.',
      examples=['celsius', 'fahrenheit'],
    ),
  ) -> Controller.AlertResponse[ForecastData | DailyForecastData | USAQIData | EAQIData | PollenData | NoneType]:
    """
    Generates environmental alerts for a specific location and service type.

    This endpoint retrieves data from external providers to generate alert
    messages based on weather, air quality, or pollen levels for a given
    latitude and longitude. The query must specify the service type (e.g.,
    weather, air-quality, pollen), and may include timezone, preferred
    temperature unit, and language for the alert message.

    For 'weather' and 'air-quality' services, the system retrieves daily data
    for the current day using the configured timezone. If the service is
    'pollen', it fetches the latest pollen index data.

    The response includes the provider name, the service type, an alert
    message crafted from the data, and the raw data used. This helps users
    quickly assess environmental risks or conditions in their area.
    """
    provider = None
    data = None
    dateinfo = None

    if service == 'weather' or service == 'air-quality':
      date = get_current_datetime(timezone)
      dateinfo = Controller.DateInfo(period='daily', start=date, end=date, timezone=timezone)

      if service == 'weather':
        provider = forecast.name

        if dateinfo.period == 'hourly':
          data = await forecast.fetch(lat=lat, lon=lon, timezone=timezone, temperature_unit=temperature_unit)
        else:
          data = await forecast.fetch_daily(lat=lat, lon=lon, dateinfo=dateinfo, temperature_unit=temperature_unit)
      elif service == 'air-quality':
        provider = air_quality.name
        data = await air_quality.fetch(lat=lat, lon=lon)
    elif service == 'pollen':
      provider = pollen.name
      data = await pollen.fetch(lon=lon, lat=lat)

    return await controller.generate_alert_response(provider, service, data, temperature_unit, dateinfo, language)
