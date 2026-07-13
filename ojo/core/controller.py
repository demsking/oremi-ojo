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
import json
import logging
import re
from datetime import datetime
from types import NoneType
from typing import Any
from typing import ClassVar
from typing import Generic
from typing import TypeVar

from pydantic import BaseModel
from pydantic import Field

from ..core.geo import Location
from ..llm.agent import AgentClient
from ..models.air_quality import EAQIData
from ..models.air_quality import USAQIData
from ..models.forecast import DailyForecastData
from ..models.forecast import ForecastData
from ..models.pollen import PollenData
from ..tools.date_tool import GetDateTool
from ..tools.date_tool import Period
from ..tools.location_tool import GetLocationTool
from ..tools.service_tool import GetServiceTool
from ..utils.date import format_date
from ..utils.date import format_datetime

ResponseData = ForecastData | DailyForecastData | USAQIData | EAQIData | PollenData
ResponseDataModel = dict[GetServiceTool.Service, ResponseData | NoneType]
MultiLocationResponseDataModel = dict[str, ResponseDataModel]
ResponsePayloadModel = ResponseDataModel | MultiLocationResponseDataModel
ResponseDataType = TypeVar('ResponseDataType', bound=BaseModel | ResponsePayloadModel | NoneType)


logger = logging.getLogger(__name__)


class Controller:
  SERVICE_NAMES: ClassVar[set[str]] = {'weather', 'air-quality', 'pollen'}
  DEFAULT_RESPONSE_TEXT: ClassVar[str] = 'No response'
  DEFAULT_WEATHER_FIELDS: ClassVar[set[str]] = {
    'temperature',
    'temperature_2m_max',
    'temperature_2m_min',
    'humidity',
    'wind_speed',
    'wind_speed_10m_max',
    'rain_sum',
    'weather_code',
  }
  WEATHER_VARIABLE_OUTPUT_FIELDS: ClassVar[dict[str, str]] = {
    'temperature': 'temperature',
    'temperature_2m': 'temperature',
    'relative_humidity_2m': 'humidity',
    'relativehumidity_2m': 'humidity',
    'humidity': 'humidity',
    'wind_speed': 'wind_speed',
    'wind_speed_10m': 'wind_speed',
    'windspeed_10m': 'wind_speed',
    'sunrise': 'sunrise',
    'sunset': 'sunset',
  }
  POLLEN_GLOSSARY_FR: ClassVar[dict[str, str]] = {
    'alder': 'aulne',
    'birch': 'bouleau',
    'grass': 'graminées',
    'grass pollen': 'pollen de graminées',
    'mugwort': 'armoise',
    'olive': 'olivier',
    'ragweed': 'ambroisie',
  }

  def __init__(self, assistant: AgentClient) -> None:
    self.assistant = assistant
    self.response_agent = assistant.create_agent(
      system=(
        'You answer weather, air-quality, and pollen questions using only the supplied data.\n'
        'If a value or service is absent, do not mention it and do not infer it.\n'
        'Never invent sky conditions, air cleanliness, wind direction, rain, alerts, or clothing advice unless the data supports it.\n'
        'If the request asks for a precise value, answer with that value first.\n'
        'For broad weather requests, summarize only the available relevant measurements.\n'
        'Do not use text in parentheses. Provide direct answers only.\n'
        "Do not start with greetings like 'Hello' or the user's name. Go straight to the point.\n"
        'Your response must:\n'
        "- Be conversational and clear in the user's requested language\n"
        '- Be concise: one or two short sentences maximum\n'
        '- Avoid listing raw JSON or repeating irrelevant fields\n'
        '- Mention the provider only if it helps clarify the source\n'
        '- Offer a recommendation only when a concrete risk is present in the data\n'
        '- Feel like a helpful assistant speaking to a human\n'
        'Your responses will be used by a text-to-speech (TTS) service. Make sure they are easy to pronounce and suitable for basic TTS engines.\n'
      )
    )

    self.language_detector_agent = assistant.create_agent(
      system=(
        'Detect the language of the provided user text and return only one BCP-47 language code in lowercase '
        '(examples: en, fr, es, pt-br, ar, sw). '
        'Do not add explanations or extra text.'
      )
    )

    self.alerts_response_agent = assistant.create_agent(
      system=(
        'You are an emergency alert specialist. Use only the supplied data. '
        'Prioritize immediate dangers and actionable advice.\n'
        'If no alert-level value is present, say there is no notable alert in one short sentence.\n\n'
        'Critical response rules:\n'
        # '1. URGENCY FIRST:\n'
        # '   - Start with the most severe threat\n'
        # '   - Never greet or use filler words\n'
        # '   - Maximum 3 sentences\n\n'
        '1. ALERT TYPE HANDLING:\n'
        '   - POLLEN: Only mention risk level 2+ (group by severity)\n'
        '   - WEATHER: Highlight only warnings (storms, heatwaves, etc.)\n'
        '   - AIR QUALITY: Report AQI 4+ (poor or dangerous)\n\n'
        # '3. STRUCTURE:\n'
        # '   [Severity] + [Threat] + [Type] + [Action]\n'
        # "   Example: 'Heatwave warning! 38°C expected. Avoid outdoor activities.'\n\n"
        '2. FORMATTING:\n'
        '   - Weather: Use ! for immediate dangers\n'
        '   - Pollen: Specify type/category (tree/grass/weed)\n'
        '   - Air Quality: Include pollutant if available\n\n'
        '3. ACTIONS:\n'
        '   Always end with one concrete recommendation\n\n'
        'Your response must:\n'
        "- Be conversational and clear in the user's requested language\n"
        '- Be concise: one or two short sentences maximum\n'
        '- Avoid listing raw JSON or irrelevant fields\n'
        '- Offer a recommendation only when a concrete risk is present in the data\n'
        'Never mention:\n'
        "- Do not start with greetings like 'Hello' or the user's name. Go straight to the point.\n"
        '- Low-risk conditions (level 1/0)\n'
        '- Technical measurements\n'
        '- Future forecasts beyond 24 hours\n'
        '- Multiple alerts of same type/severity\n'
        '- Avoid any formating or new lines.\n'
        'Your responses will be used by a text-to-speech (TTS) service. Make sure they are easy to pronounce and suitable for basic TTS engines.\n'
      )
    )

    self.date_agent = GetDateTool(
      assistant=assistant,
    )

    self.location_agent = GetLocationTool(
      assistant=assistant,
    )

    self.service_agent = GetServiceTool(
      assistant=assistant,
    )

  @staticmethod
  def _compact_value(value: Any) -> Any:
    if isinstance(value, str) and ':' in value:
      return value

    if isinstance(value, float):
      return round(value, 1)

    if isinstance(value, str):
      match = re.fullmatch(r'(-?\d+(?:\.\d+)?)(.*)', value.strip())

      if match and match.group(2).strip():
        suffix = match.group(2).strip()
        separator = '' if suffix.startswith(('°', '%')) else ' '

        return f'{round(float(match.group(1)), 1)}{separator}{suffix}'

    return value

  @staticmethod
  def _compact_data(value: Any) -> Any:
    if isinstance(value, dict):
      return {key: Controller._compact_data(item) for key, item in value.items()}

    if isinstance(value, list):
      return [Controller._compact_data(item) for item in value]

    return Controller._compact_value(value)

  @staticmethod
  def _requested_weather_fields(requested_fields: set[str] | None) -> set[str]:
    if not requested_fields:
      return set(Controller.DEFAULT_WEATHER_FIELDS)

    return {Controller.WEATHER_VARIABLE_OUTPUT_FIELDS.get(field, field) for field in requested_fields}

  def _format_service_data_map(
    self,
    data: dict[str, ResponseData | NoneType],
    *,
    requested_data_fields: dict[str, set[str]] | None = None,
  ) -> dict[str, Any]:
    prompt_data: dict[str, Any] = {}

    for service, service_data in data.items():
      if isinstance(service_data, BaseModel):
        service_payload = service_data.model_dump(exclude_none=True)
      else:
        service_payload = service_data

      if service == 'weather' and isinstance(service_payload, dict):
        weather_fields = Controller._requested_weather_fields((requested_data_fields or {}).get(service))
        service_payload = {
          key: value for key, value in service_payload.items() if key in weather_fields and value not in (None, '', [], {})
        }

      prompt_data[service] = Controller._compact_data(service_payload)

    return prompt_data

  def _format_prompt_data(
    self,
    data: ResponsePayloadModel | ResponseData | NoneType,
    *,
    requested_data_fields: dict[str, set[str]] | None = None,
  ) -> str:
    prompt_payload = self._relevant_prompt_payload(data, requested_data_fields=requested_data_fields)

    return json.dumps(prompt_payload, ensure_ascii=False)

  def _relevant_prompt_payload(
    self,
    data: ResponsePayloadModel | ResponseData | NoneType,
    *,
    requested_data_fields: dict[str, set[str]] | None = None,
  ) -> Any:
    if data is None:
      return {'error': 'Unable to fetch data for the specified location'}

    if isinstance(data, BaseModel):
      return Controller._compact_data(data.model_dump(exclude_none=True))

    if isinstance(data, dict):
      keys = list(data.keys())

      if keys and all(key in Controller.SERVICE_NAMES for key in keys):
        service_data_map: dict[str, ResponseData | NoneType] = {
          str(service): service_data for service, service_data in data.items() if not isinstance(service_data, dict)
        }
        return self._format_service_data_map(service_data_map, requested_data_fields=requested_data_fields)

      payload_by_location: dict[str, Any] = {}

      for location_name, location_data in data.items():
        if isinstance(location_data, dict):
          location_service_map: dict[str, ResponseData | NoneType] = {
            str(service): service_data for service, service_data in location_data.items() if not isinstance(service_data, dict)
          }
          relevant_data = self._format_service_data_map(
            location_service_map,
            requested_data_fields=requested_data_fields,
          )

          if relevant_data:
            payload_by_location[location_name] = relevant_data
        else:
          payload_by_location[location_name] = Controller._compact_data(location_data)

      return payload_by_location

    return str(data)

  @staticmethod
  def _date_prompt_context(dateinfo: 'Controller.DateInfo | None') -> str:
    if not dateinfo:
      return ''

    if dateinfo.start == dateinfo.end:
      now = datetime.now(dateinfo.start.tzinfo).replace(second=0, microsecond=0)

      if dateinfo.start.date() == now.date():
        return f'Current date and time: {format_datetime(now)}.'

      return f'Date: {dateinfo.start_date}.'

    return f'Start date: {dateinfo.start_date}.\nEnd date: {dateinfo.end_date}.'

  @staticmethod
  def _extract_generated_text(result: Any) -> str:
    return result.response if result and result.response else Controller.DEFAULT_RESPONSE_TEXT

  @staticmethod
  def _translation_glossary_instruction(target_language: str) -> str:
    if not target_language.startswith('fr'):
      return ''

    glossary = '\n'.join(f'- {source} => {target}' for source, target in Controller.POLLEN_GLOSSARY_FR.items())

    return f'Pollen terminology glossary (mandatory):\n{glossary}\n'

  @staticmethod
  def _normalize_language_code(language: str | None) -> str:
    normalized = (language or '').strip().lower().replace('_', '-')

    if not normalized:
      return 'en'

    return normalized.split()[0].strip('`"\'.,;:!?()[]{}') or 'en'

  @staticmethod
  def _looks_like_language_code(language: str) -> bool:
    return bool(language) and ' ' not in language and all(part.isalpha() for part in language.split('-'))

  @staticmethod
  def _language_instruction(target_language: str) -> str:
    normalized = Controller._normalize_language_code(target_language)

    if normalized.startswith('fr'):
      return 'The user request is written in French. Reply in French.'

    if normalized.startswith('en'):
      return 'The user request is written in English. Reply in English.'

    return f'The user request is written in {normalized}. Reply in the same language.'

  @staticmethod
  def _response_language_prompt(target_language: str | None) -> str:
    normalized = Controller._normalize_language_code(target_language)
    instruction = Controller._language_instruction(normalized)
    glossary = Controller._translation_glossary_instruction(normalized)

    if glossary:
      return f'{instruction}\n{glossary}'

    return instruction

  async def detect_language(self, user_input: str) -> str:
    result = await self.language_detector_agent.generate(user_input)
    raw_language = Controller._extract_generated_text(result).strip().lower()
    normalized = Controller._normalize_language_code(raw_language)

    if (
      not raw_language
      or raw_language == Controller.DEFAULT_RESPONSE_TEXT.lower()
      or not Controller._looks_like_language_code(normalized)
    ):
      return 'en'

    return normalized

  async def generate_response(
    self,
    user_input: str,
    provider: str,
    location: Location,
    services: list[GetServiceTool.Service],
    data: ResponsePayloadModel,
    temperature_unit: str,
    dateinfo: 'Controller.DateInfo | None',
    language: str | None = None,
    requested_data_fields: dict[str, set[str]] | None = None,
  ) -> 'Controller.Response[ResponsePayloadModel]':
    prompt_data = self._format_prompt_data(data, requested_data_fields=requested_data_fields)
    response_language = language or await self.detect_language(user_input)

    prompt_lines = [
      f'User request: {user_input}',
      Controller._response_language_prompt(response_language),
      f'Data source: {provider}',
      f'Temperature unit: {temperature_unit}',
      f'Relevant data only: {prompt_data}',
      'Answer only from the relevant data. Do not mention missing services or absent fields.',
    ]
    date_context = Controller._date_prompt_context(dateinfo)

    if date_context:
      prompt_lines.append(date_context)

    prompt = '\n'.join(prompt_lines)
    result = await self.response_agent.generate(prompt)
    message = Controller._extract_generated_text(result)

    logger.debug(f'Generated response: {message}')

    return Controller.Response(
      input=user_input,
      services=services,
      provider=provider,
      message=message,
      location=location,
      data=data,
    )

  async def generate_alert_response(
    self,
    provider: str,
    service: GetServiceTool.Service,
    data: ResponseData | NoneType,
    temperature_unit: str,
    dateinfo: 'Controller.DateInfo | None',
    language: str | None = None,
    requested_data_fields: dict[str, set[str]] | None = None,
  ) -> 'Controller.AlertResponse[ResponseData | NoneType]':
    prompt_data = self._format_prompt_data(data, requested_data_fields=requested_data_fields)

    prompt_lines = [
      Controller._response_language_prompt(language),
      f'Data source: {provider}',
      f'Temperature unit: {temperature_unit}',
      f'Relevant data only: {prompt_data}',
      'Answer only from the relevant data. Do not mention missing services or absent fields.',
    ]
    date_context = Controller._date_prompt_context(dateinfo)

    if date_context:
      prompt_lines.append(date_context)

    prompt = '\n'.join(prompt_lines)

    result = await self.alerts_response_agent.generate(prompt)
    message = Controller._extract_generated_text(result)

    logger.debug(f'Generated alert response: {message}')

    return Controller.AlertResponse(
      service=service,
      provider=provider,
      message=message,
      data=data,
    )

  async def get_date(self, user_input: str, *, timezone: str) -> 'Controller.DateInfo':
    tool, start, end = await self.date_agent.get_date(user_input, timezone=timezone)
    period = GetDateTool.period_map[tool.name]  # type: ignore

    return Controller.DateInfo(
      period=period,
      start=start,
      end=end,
      timezone=timezone,
    )

  class DateInfo(BaseModel):
    period: Period
    start: datetime
    end: datetime
    timezone: str

    @property
    def start_date(self) -> str:
      return format_date(self.start)

    @property
    def end_date(self) -> str:
      return format_date(self.end)

    @property
    def start_datetime(self) -> str:
      return format_datetime(self.start)

    @property
    def end_datetime(self) -> str:
      return format_datetime(self.end)

  class Response(BaseModel, Generic[ResponseDataType]):
    provider: str = Field(..., description='Name of the data provider')
    input: str = Field(..., description='User input that triggered the response')
    services: list[GetServiceTool.Service] = Field(..., description='List of services used for generating the response')
    message: str = Field(..., description='Message or explanation related to the response')
    data: ResponseDataType | None = Field(..., description='Structured data returned by the provider')
    location: Location = Field(..., description='Location information related to the response')

  class AlertResponse(BaseModel, Generic[ResponseDataType]):
    provider: str = Field(..., description='Name of the data provider')
    service: GetServiceTool.Service = Field(..., description='Service used for generating the response')
    message: str = Field(..., description='Message or explanation related to the response')
    data: ResponseDataType | None = Field(..., description='Structured data returned by the provider')
