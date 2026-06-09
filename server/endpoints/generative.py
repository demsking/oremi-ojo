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
import asyncio
from types import NoneType
from typing import Any

from fastapi import FastAPI
from fastapi import HTTPException
from fastapi import Query

from ..core.controller import Controller
from ..core.controller import ResponseData
from ..core.controller import ResponseDataModel
from ..core.time import get_current_datetime
from ..providers.OpenMeteoAirQualityProvider import AirQualityData
from ..providers.OpenMeteoAirQualityProvider import OpenMeteoAirQualityProvider
from ..providers.OpenMeteoForecastProvider import ForecastData
from ..providers.OpenMeteoForecastProvider import OpenMeteoForecastProvider
from ..providers.OpenMeteoForecastProvider import TemperatureUnit
from ..providers.OpenMeteoPollenProvider import OpenMeteoPollenProvider
from ..providers.OpenMeteoPollenProvider import PollenData
from ..tools.service_tool import GetServiceTool


def _dedupe_locations(locations: list[Any]) -> list[Any]:
  seen: set[tuple[float, float]] = set()
  deduped: list[Any] = []

  for location in locations:
    key = (location.lat, location.lon)

    if key in seen:
      continue

    seen.add(key)
    deduped.append(location)

  return deduped


def _dedupe_services(services: list[GetServiceTool.Service]) -> list[GetServiceTool.Service]:
  seen: set[GetServiceTool.Service] = set()
  deduped: list[GetServiceTool.Service] = []

  for service in services:
    if service not in seen:
      seen.add(service)
      deduped.append(service)

  return deduped


def create_generative_endpoints(
  tag: str,
  api: FastAPI,
  controller: Controller,
  forecast: OpenMeteoForecastProvider,
  air_quality: OpenMeteoAirQualityProvider,
  pollen: OpenMeteoPollenProvider,
) -> None:
  example_response = Controller.Response[ForecastData | AirQualityData | PollenData].model_validate(
    {
      'provider': 'Open-Météo',
      'services': ['weather'],
      'input': "Quel temps fait à Paris aujourd'hui ?",
      'message': "Il fait 12 degrés Celsius à Paris aujourd'hui, avec une humideur de 37 pour cent et un vent doux à 4,3 kilomètres par heure. Il commence à se lever à 7h13 et se couche à 20h31. C'est un excellent temps pour sortir et profiter du soleil.",
      'message_language': 'fr',
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
      460: {
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
        'Quel temps fait-il a Villiers-sur-Marne et Paris ?',
        'Quel temps fait-il actuellement a Paris ? Y a-t-il du pollen a Villiers-sur-Marne ?',
        'What is the air quality in Paris today?',
        'Compare air quality in Paris and Lyon today',
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
  ) -> Controller.Response[ResponseDataModel | dict[str, ResponseDataModel]]:
    """
    Generate a natural-language climate response from free-form user input.

    The endpoint can resolve multiple requested services (weather, air quality,
    pollen) and multiple mentioned locations in one request. With one location,
    the payload is a service-to-data map. With multiple locations, the payload
    becomes a location-to-service-data map.

    If no service can be identified, it returns a service-identification error.
    If no location can be resolved, it returns a location error.
    """
    calls, locations_from_text = await asyncio.gather(
      controller.service_agent.get_user_input_services(q, timezone=timezone),
      controller.location_agent.get_user_input_locations(q, limit=5),
    )

    if calls:
      requested_services = _dedupe_services([service for service, _, _ in calls if service])
      locations_from_calls = [call_location for _, call_location, _ in calls if call_location]
      locations = _dedupe_locations(locations_from_calls + locations_from_text)

      if locations:
        providers: set[str] = set()
        data: ResponseDataModel | dict[str, ResponseDataModel]
        dateinfo = None

        if 'weather' in requested_services or 'air-quality' in requested_services:
          dateinfo = await controller.get_date(q, timezone=timezone)

        async def fetch_location_data(location: Any) -> ResponseDataModel:
          location_tasks: dict[GetServiceTool.Service, Any] = {}

          # Helper to retrieve extracted variables for this location and service
          def get_vars(service_name: str):
            sh_vars, sd_vars, s_vars = None, None, None

            for call_service, call_loc, call_args in calls:
              if call_service == service_name:
                is_match = False

                if call_loc:
                  is_match = abs(call_loc.lat - location.lat) < 0.1 and abs(call_loc.lon - location.lon) < 0.1
                else:
                  is_match = len(locations) == 1

                if is_match and call_args:
                  if service_name == 'weather':
                    sh_vars = call_args.get('hourly_variables')
                    sd_vars = call_args.get('daily_variables')
                  elif service_name == 'air-quality':
                    s_vars = call_args.get('variables')
                  break

            if not sh_vars and not sd_vars and not s_vars:
              h_union, d_union, v_union = [], [], []

              for call_service, _, call_args in calls:
                if call_service == service_name and call_args:
                  if service_name == 'weather':
                    if call_args.get('hourly_variables'):
                      h_union.extend(call_args.get('hourly_variables'))  # type: ignore

                    if call_args.get('daily_variables'):
                      d_union.extend(call_args.get('daily_variables'))  # type: ignore
                  elif service_name == 'air-quality':
                    if call_args.get('variables'):
                      v_union.extend(call_args.get('variables'))  # type: ignore

              if h_union:
                sh_vars = list(set(h_union))

              if d_union:
                sd_vars = list(set(d_union))

              if v_union:
                s_vars = list(set(v_union))
            return sh_vars, sd_vars, s_vars

          if 'weather' in requested_services:
            providers.add(forecast.name)
            sh_vars, sd_vars, _ = get_vars('weather')

            if dateinfo and dateinfo.period == 'hourly':
              location_tasks['weather'] = forecast.fetch(
                lat=location.lat,
                lon=location.lon,
                timezone=timezone,
                temperature_unit=temperature_unit,
                hourly_variables=sh_vars,
                daily_variables=sd_vars,
              )
            else:
              location_tasks['weather'] = forecast.fetch_daily(
                lat=location.lat,
                lon=location.lon,
                dateinfo=dateinfo,  # type: ignore[arg-type]
                temperature_unit=temperature_unit,
                daily_variables=sd_vars,
              )

          if 'air-quality' in requested_services:
            providers.add(air_quality.name)
            _, _, s_vars = get_vars('air-quality')
            location_tasks['air-quality'] = air_quality.fetch(lat=location.lat, lon=location.lon, variables=s_vars)

          if 'pollen' in requested_services:
            providers.add(pollen.name)
            location_tasks['pollen'] = pollen.fetch(lon=location.lon, lat=location.lat)

          if not location_tasks:
            return {}

          fetched_values = await asyncio.gather(*location_tasks.values())
          return {service: value for service, value in zip(location_tasks.keys(), fetched_values, strict=False)}

        location_payloads = await asyncio.gather(*(fetch_location_data(location) for location in locations))

        if len(locations) == 1:
          data = location_payloads[0]
        else:
          data = {location.display_name: payload for location, payload in zip(locations, location_payloads, strict=False)}

        if providers and requested_services:
          primary_location = locations[0]
          locale = primary_location.address.country_code if primary_location.address else None
          provider = ', '.join(sorted(providers))

          return await controller.generate_response(
            q,
            provider,
            primary_location,
            requested_services,
            data,
            temperature_unit,
            dateinfo,
            locale=locale,
          )

      raise HTTPException(status_code=400, detail='No location found for user input')
    raise HTTPException(status_code=460, detail='Unable to identify service for user input')

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
      503: {
        'description': 'Unable to identify provider for requested service',
        'content': {
          'application/json': {'example': {'detail': 'Unable to identify provider for requested service'}},
        },
      },
    },
  )
  async def generate_alerts_info(
    service: GetServiceTool.Service = Query(
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
  ) -> Controller.AlertResponse[ResponseData | NoneType]:
    """
    Generate alert-focused responses for one service at one location.

    The endpoint fetches weather, air-quality, or pollen data for the provided
    coordinates and asks the alert agent to produce a concise warning message
    in the requested language.

    It returns provider metadata, service name, generated alert message, and
    the structured source data used by the LLM.
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

    if not provider:
      raise HTTPException(status_code=503, detail='Unable to identify provider for requested service')

    return await controller.generate_alert_response(provider, service, data, temperature_unit, dateinfo, language)
