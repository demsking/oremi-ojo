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

ResponseData = ForecastData | DailyForecastData | USAQIData | EAQIData | PollenData
ResponseDataModel = dict[GetServiceTool.Service, ResponseData | NoneType]
MultiLocationResponseDataModel = dict[str, ResponseDataModel]
ResponsePayloadModel = ResponseDataModel | MultiLocationResponseDataModel
ResponseDataType = TypeVar('ResponseDataType', bound=BaseModel | ResponsePayloadModel | NoneType)


logger = logging.getLogger(__name__)


class Controller:
  SERVICE_NAMES: ClassVar[set[str]] = {'weather', 'air-quality', 'pollen'}
  DEFAULT_RESPONSE_TEXT: ClassVar[str] = 'No response'
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
        "You are a smart weather assistant. Respond to the user's weather request in a natural, clear, and human-like way, "
        'Use the forecast data provided in the context to generate your response.\n'
        'Do not use text in parentheses. Provide direct answers only.\n'
        "Do not start with greetings like 'Hello' or the user's name. Go straight to the point.\n"
        'Your response must:\n'
        "- Be conversational and clear in the user's requested language\n"
        '- Avoid listing raw data\n'
        "- Subtly mention the source of the data by extracting the provider's name from the context\n"
        '- Offer a recommendation when relevant (e.g., dress warmly, take an umbrella, avoid strong winds)\n'
        '- Feel like a helpful assistant speaking to a human\n'
        '- Always use short, simple sentences\n'
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
        'You are an emergency alert specialist. Deliver urgent notifications about weather, pollen, and air quality risks. '
        'Prioritize immediate dangers and actionable advice using active alerts.\n\n'
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
        '- Avoid listing raw data\n'
        "- Subtly mention the source of the data by extracting the provider's name from the context\n"
        '- Offer a recommendation when relevant (e.g., dress warmly, take an umbrella, avoid strong winds)\n'
        '- Feel like a helpful assistant speaking to a human\n'
        '- Always use short, simple sentences\n'
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

  def _format_service_data_map(self, data: dict[str, ResponseData | NoneType]) -> dict[str, Any]:
    return {
      service: (service_data.model_dump() if isinstance(service_data, BaseModel) else service_data)
      for service, service_data in data.items()
    }

  def _format_prompt_data(self, data: ResponsePayloadModel | ResponseData | NoneType) -> str:
    if data is None:
      return 'Response: Unable to fetch data for the specified location'

    if isinstance(data, BaseModel):
      return data.model_dump_json()

    if isinstance(data, dict):
      keys = list(data.keys())

      if keys and all(key in Controller.SERVICE_NAMES for key in keys):
        service_data_map: dict[str, ResponseData | NoneType] = {
          str(service): service_data for service, service_data in data.items() if not isinstance(service_data, dict)
        }
        return json.dumps(self._format_service_data_map(service_data_map), ensure_ascii=False)

      payload_by_location: dict[str, Any] = {}

      for location_name, location_data in data.items():
        if isinstance(location_data, dict):
          location_service_map: dict[str, ResponseData | NoneType] = {
            str(service): service_data for service, service_data in location_data.items() if not isinstance(service_data, dict)
          }
          payload_by_location[location_name] = self._format_service_data_map(location_service_map)
        else:
          payload_by_location[location_name] = location_data

      return json.dumps(payload_by_location, ensure_ascii=False)

    return str(data)

  @staticmethod
  def _date_prompt_context(dateinfo: 'Controller.DateInfo | None') -> str:
    if not dateinfo:
      return ''

    if dateinfo.start == dateinfo.end:
      today = datetime.now()

      if dateinfo.start.date() == today.date():
        return f'Current Date and Time: {today}.'

      return f'Date: {dateinfo.start_date}.'

    return f'Start Date: {dateinfo.start_date}.\nEnd Date: {dateinfo.end_date}.'

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
  ) -> 'Controller.Response[ResponsePayloadModel]':
    prompt_data = self._format_prompt_data(data)
    response_language = language or await self.detect_language(user_input)

    prompt = (
      f'User Request: {user_input}.\n'
      f'{Controller._response_language_prompt(response_language)}\n'
      f'Provider: {provider}.\n'
      f'Services: {", ".join(services)}.\n'
      f'{prompt_data}.\n'
      f'Temperature Unit: {temperature_unit}'
    )

    prompt += Controller._date_prompt_context(dateinfo)

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
  ) -> 'Controller.AlertResponse[ResponseData | NoneType]':
    prompt_data = self._format_prompt_data(data)

    prompt = (
      f'{Controller._response_language_prompt(language)}\n'
      f'Provider: {provider}.\nProvider Response: {prompt_data}.\nTemperature Unit: {temperature_unit}\n'
    )
    prompt += Controller._date_prompt_context(dateinfo)

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
      return self.start.date().isoformat()

    @property
    def end_date(self) -> str:
      return self.end.date().isoformat()

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
