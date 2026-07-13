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
from typing import Any

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.openapi.models import Example

from ..core.controller import Controller
from ..core.controller import ResponseDataModel
from ..core.geo import Location
from ..core.models import ProcessRequest
from ..core.models import ProcessResponse
from ..models.air_quality import AirQualityData
from ..models.forecast import ForecastData
from ..models.pollen import PollenData
from ..services.air_quality_service import AirQualityService
from ..services.forcast_service import ForecastService
from ..services.forcast_service import TemperatureUnit
from ..services.pollen_service import PollenService
from ..tools.service_tool import GetServiceTool


API_TAG_METADATA = {
  'name': 'Agent Processing',
  'description': (
    'Endpoints for generating climate information, such as weather, air quality, '
    'and pollen data, based on user input. These endpoints process queries to '
    'provide relevant and accurate responses.'
  ),
}


router = APIRouter(prefix='/agent', tags=[API_TAG_METADATA['name']])


PAYLOAD_EXAMPLES: dict[str, Example] = {
  # --- WEATHER ---
  'Weather forecast (EN)': {
    'summary': 'Weather forecast (EN)',
    'description': 'Requesting weather details with localized imperial/metric preferences via context.',
    'value': ProcessRequest.model_validate(
      {
        'message': "What's the weather like in Lagos?",
        'context': {'timezone': 'Africa/Lagos', 'temperature_unit': 'celsius'},
      }
    ),
  },
  'Météo (FR)': {
    'summary': 'Prévisions météo (FR)',
    'description': "Demande d'informations météo pour une ville spécifique.",
    'value': ProcessRequest.model_validate(
      {
        'message': 'Quel temps fait-il à Paris ?',
        'context': {
          'location': 'Paris, France',
          'timezone': 'Europe/Paris',
          'temperature_unit': 'celsius',
          'measurement_system': 'metric',
          'distance_unit': 'kilometer',
          'latitude': 48.856614,
          'longitude': 2.3522219,
        },
      }
    ),
  },
  'Sunset time (EN)': {
    'summary': 'Sunset time (EN)',
    'description': 'Asks for the expected sunset time and evening weather conditions.',
    'value': ProcessRequest.model_validate(
      {
        'message': 'What time does the sun set in Reykjavik tonight?',
        'context': {'timezone': 'Atlantic/Reykjavik', 'temperature_unit': 'celsius'},
      }
    ),
  },
  'Wind and sunrise (EN)': {
    'summary': 'Wind and sunrise (EN)',
    'description': 'Requests current wind strength and sunrise timing for a specific location.',
    'value': ProcessRequest.model_validate(
      {
        'message': 'How windy is it in Nairobi this morning and when does sunrise happen?',
        'context': {'timezone': 'Africa/Nairobi', 'temperature_unit': 'celsius'},
      }
    ),
  },
  'Lever du soleil et vitesse du vent (FR)': {
    'summary': 'Lever du soleil (FR)',
    'description': "Demande d'informations sur le lever du soleil et le vent.",
    'value': ProcessRequest.model_validate(
      {
        'message': "À quelle heure le soleil se lève à Douala aujourd'hui, et quel est le la vitesse du vent ?",
        'context': {'timezone': 'Africa/Douala', 'temperature_unit': 'celsius'},
      }
    ),
  },
  'Coucher du soleil (FR)': {
    'summary': 'Coucher du soleil (FR)',
    'description': "Demande d'informations sur le coucher du soleil.",
    'value': ProcessRequest.model_validate(
      {
        'message': "À quelle heure le soleil se couche à Yaoundé aujourd'hui ?",
        'context': {'timezone': 'Africa/Douala', 'temperature_unit': 'celsius'},
      }
    ),
  },
  # --- POLLEN ---
  'Pollen count (EN)': {
    'summary': 'Pollen & Allergen report (EN)',
    'description': 'Checks local pollen levels using geography coordinates.',
    'value': ProcessRequest.model_validate(
      {
        'message': 'Are pollen levels high in Lyon today?',
        'context': {'lat': 45.7640, 'lon': 4.8357, 'timezone': 'Europe/Paris'},
      }
    ),
  },
  'Alerte Pollen (FR)': {
    'summary': 'Indice de pollen (FR)',
    'description': "Vérification des risques d'allergies aux pollens (RNSA).",
    'value': ProcessRequest.model_validate(
      {
        'message': "Est-ce qu'il y a du pollen à Lyon en ce moment ?",
        'context': {'lat': 45.7640, 'lon': 4.8357, 'timezone': 'Europe/Paris'},
      }
    ),
  },
}

RESPONSE_EXAMPLES: dict[str, Example] = {
  # --- WEATHER ---
  'weather': {
    'summary': 'Weather response',
    'value': ProcessResponse[ForecastData | AirQualityData | PollenData].model_validate(
      {
        'ok': True,
        'input': "What's the weather like in Lagos?",
        'services': ['weather'],
        'message': 'It is hot today in Lagos, with a temperature of 26.2 degrees Celsius. The air feels very humid at around 88%. There are light winds blowing gently from the west to help cool you down. Sunshine will be present this morning and throughout most of the day as it sets early tonight. Dress lightly but stay hydrated since there is high moisture in the atmosphere.',
        'data': {
          'weather': {
            'temperature': '26.2°C',
            'humidity': '88%',
            'wind_speed': '8.1 km/h',
            'sunrise': '06:37:00',
            'sunset': '19:05:00',
          }
        },
        'location': {
          'type': 'city',
          'name': 'Lagos',
          'boundingbox': [6.2950575, 6.6150575, 3.2341795, 3.5541795],
          'lat': 6.4550575,
          'lon': 3.3941795,
          'addresstype': 'city',
          'display_name': 'Lagos, Lagos Island, Lagos State, 100242, Nigeria',
          'address': {
            'country': 'Nigeria',
            'country_code': 'ng',
            'postcode': '100242',
            'county': 'Lagos Island',
            'state': 'Lagos State',
            'city': 'Lagos',
          },
        },
        'confidence': 1.0,
      }
    ),
  },
}


def _context_value(context: dict[str, Any], *keys: str, default: Any = None) -> Any:
  for key in keys:
    if key in context and context[key] not in (None, ''):
      return context[key]

    if key in context and context[key] not in (None, ''):
      return context[key]

  return default


def _context_location(context: dict[str, Any]) -> Location | None:
  lat = _context_value(context, 'lat', 'latitude')
  lon = _context_value(context, 'lon', 'longitude')

  if lat is None or lon is None:
    return None

  name = str(_context_value(context, 'location', 'display_name', 'name', default='Current location'))

  return Location.model_validate(
    {
      'type': 'context',
      'name': name,
      'boundingbox': [float(lat), float(lat), float(lon), float(lon)],
      'lat': float(lat),
      'lon': float(lon),
      'addresstype': 'context',
      'display_name': name,
      'address': {
        'country': str(_context_value(context, 'country', default='Unknown')),
        'country_code': str(_context_value(context, 'country_code', default='')),
      },
    }
  )


def _is_alert_route(context: dict[str, Any]) -> bool:
  route_value = _context_value(context, 'endpoint', 'route', 'response_type', 'intent', default='')

  return isinstance(route_value, str) and 'alert' in route_value.lower()


def _dedupe_locations(locations: list[Any]) -> list[Any]:
  deduped: list[Any] = []

  for location in locations:
    is_duplicate = any(
      abs(existing.lat - location.lat) < 0.1 and abs(existing.lon - location.lon) < 0.1 for existing in deduped
    )

    if is_duplicate:
      continue

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


def _primary_service(services: list[GetServiceTool.Service]) -> GetServiceTool.Service:
  if len(services) != 1:
    raise HTTPException(status_code=400, detail='Alert responses require exactly one requested service')

  return services[0]


@router.post(
  path='/chat',
  summary='Process a natural-language request',
  response_model=ProcessResponse,
  status_code=status.HTTP_200_OK,
  responses={
    200: {
      'description': (
        'The request was processed. Inspect `ok` to distinguish a successful result from an expected service or input failure.'
      ),
      'content': {'application/json': {'examples': RESPONSE_EXAMPLES}},
    },
    500: {
      'description': 'An unexpected processing error occurred.',
      'content': {'application/json': {'example': {'detail': 'Internal Server Error'}}},
    },
  },
)
async def process_user_input(
  request: Request,
  payload: ProcessRequest = Body(
    ...,
    description="The user's text plus optional context.",
    openapi_examples=PAYLOAD_EXAMPLES,
  ),
) -> ProcessResponse:
  """
  Process one natural-language agent request.

  Route metadata in the request context decides whether the request should use
  the regular response generator or the alert-focused response generator.
  """
  controller: Controller = request.app.state.controller
  forecast: ForecastService = request.app.state.forecast_service
  air_quality: AirQualityService = request.app.state.air_quality_service
  pollen: PollenService = request.app.state.pollen_service

  user_request = payload.message
  context = payload.context
  context_text = str(_context_value(context, 'text', 'context', default=''))
  timezone = str(_context_value(context, 'timezone', default='UTC'))
  temperature_unit: TemperatureUnit = _context_value(context, 'temperature_unit', default='celsius')
  context_location = _context_location(context)

  calls, locations_from_text = await asyncio.gather(
    controller.service_agent.get_user_input_services(user_request, timezone=timezone, context=context_text),
    controller.location_agent.get_user_input_locations(user_request, limit=5),
  )

  if calls:
    requested_services = _dedupe_services([service for service, _, _ in calls if service])
    locations_from_calls = [call_location for _, call_location, _ in calls if call_location]
    context_locations = [context_location] if context_location else []
    locations = _dedupe_locations(locations_from_calls + locations_from_text + context_locations)

    if locations:
      providers: set[str] = set()
      data: ResponseDataModel | dict[str, ResponseDataModel]
      dateinfo = None

      if 'weather' in requested_services or 'air-quality' in requested_services:
        dateinfo = await controller.get_date(user_request, timezone=timezone)

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
        return dict(zip(location_tasks.keys(), fetched_values, strict=False))

      location_payloads = await asyncio.gather(*(fetch_location_data(location) for location in locations))

      if len(locations) == 1:
        data = location_payloads[0]
      else:
        data = {location.display_name: payload for location, payload in zip(locations, location_payloads, strict=False)}

      if providers and requested_services:
        primary_location = locations[0]
        provider = ', '.join(sorted(providers))
        language = await controller.detect_language(user_request)

        if _is_alert_route(context):
          service = _primary_service(requested_services)
          service_data = data.get(service) if len(locations) == 1 and isinstance(data, dict) else None

          if isinstance(service_data, dict):
            service_data = None

          alert = await controller.generate_alert_response(
            provider,
            service,
            service_data,
            temperature_unit,
            dateinfo,
            language=language,
          )

          return ProcessResponse(
            input=user_request,
            services=[alert.service],
            message=alert.message,
            data=alert.data,
            location=primary_location,
            confidence=1.0,
          )

        response = await controller.generate_response(
          user_request,
          provider,
          primary_location,
          requested_services,
          data,
          temperature_unit,
          dateinfo,
          language=language,
        )

        return ProcessResponse(
          input=response.input,
          services=response.services,
          message=response.message,
          data=response.data,
          location=response.location,
          confidence=1.0,
        )

    raise HTTPException(status_code=400, detail='No location found for user input')
  raise HTTPException(status_code=460, detail='Unable to identify service for user input')
