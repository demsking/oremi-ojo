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

from ..core.assistant import Assistant
from ..core.geo import Location
from ..models.air_quality import EAQIData
from ..models.air_quality import USAQIData
from ..models.forecast import DailyForecastData
from ..models.forecast import ForecastData
from ..models.pollen import PollenData
from ..models.pollen import PollenName
from ..models.pollen import PollenSeverity
from ..tools.date_tool import GetDateTool
from ..tools.date_tool import Period
from ..tools.location_tool import GetLocationTool
from ..tools.service_tool import GetServiceTool

ResponseData = ForecastData | DailyForecastData | USAQIData | EAQIData | PollenData
ResponseDataModel = dict[GetServiceTool.Service, ResponseData | NoneType]
MultiLocationResponseDataModel = dict[str, ResponseDataModel]
ResponsePayloadModel = ResponseDataModel | MultiLocationResponseDataModel
ResponseDataType = TypeVar('ResponseDataType', bound=BaseModel | ResponsePayloadModel | NoneType)


class Controller:
  SERVICE_NAMES: ClassVar[set[str]] = {'weather', 'air-quality', 'pollen'}

  POLLEN_NAME_FR: ClassVar[dict[PollenName, str]] = {
    PollenName.ALDER: 'aulne',
    PollenName.BIRCH: 'bouleau',
    PollenName.GRASS: 'graminées',
    PollenName.MUGWORT: 'armoise',
    PollenName.OLIVE: 'olivier',
    PollenName.RAGWEED: 'ambroisie',
  }

  POLLEN_SEVERITY_FR: ClassVar[dict[PollenSeverity, str]] = {
    PollenSeverity.ZERO: 'nul',
    PollenSeverity.LOW: 'faible',
    PollenSeverity.MODERATE: 'modéré',
    PollenSeverity.HIGH: 'élevé',
    PollenSeverity.VERY_HIGH: 'très élevé',
  }

  def __init__(self, assistant: Assistant, logger: logging.Logger) -> None:
    self.logger = logger
    self.assistant = assistant
    self.response_agent = assistant.create_agent(
      system=(
        "You are a smart weather assistant. Respond to the user's weather request in a natural, clear, and human-like way, "
        "using the same language as the user's request. Use the forecast data provided in the context to generate your response.\n"
        'Do not use text in parentheses. Provide direct answers only.\n'
        "Do not start with greetings like 'Hello', 'Bonjour', or the user's name. Go straight to the point.\n"
        'Your response must:\n'
        "- Be conversational and adapted to the user's language\n"
        '- Avoid listing raw data\n'
        "- Subtly mention the source of the data by extracting the provider's name from the context\n"
        '- Offer a recommendation when relevant (e.g., dress warmly, take an umbrella, avoid strong winds)\n'
        '- Feel like a helpful assistant speaking to a human\n'
        '- Always use short, simple sentences\n'
        'Your responses will be used by a text-to-speech (TTS) service. Make sure they are easy to pronounce and suitable for basic TTS engines.\n'
      )
    )

    self.alerts_response_agent = assistant.create_agent(
      system=(
        'You are an emergency alert specialist. Deliver urgent notifications about weather, pollen, and air quality risks. '
        "Prioritize immediate dangers and actionable advice. Respond in the user's language using only active alerts.\n\n"
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
        "- Be conversational and adapted to the user's language\n"
        '- Avoid listing raw data\n'
        "- Subtly mention the source of the data by extracting the provider's name from the context\n"
        '- Offer a recommendation when relevant (e.g., dress warmly, take an umbrella, avoid strong winds)\n'
        '- Feel like a helpful assistant speaking to a human\n'
        '- Always use short, simple sentences\n'
        'Never mention:\n'
        "- Do not start with greetings like 'Hello', 'Bonjour', or the user's name. Go straight to the point.\n"
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
      logger=logger,
    )

    self.location_agent = GetLocationTool(
      assistant=assistant,
      logger=logger,
    )

    self.service_agent = GetServiceTool(
      assistant=assistant,
      logger=logger,
    )

  @staticmethod
  def _is_french_locale(locale: str | None) -> bool:
    return bool(locale and locale.lower().startswith('fr'))

  def _localize_pollen_for_prompt(self, data: PollenData | None, *, locale: str | None) -> dict[str, Any] | PollenData | None:
    if not self._is_french_locale(locale) or not isinstance(data, PollenData):
      return data

    pollen_names = [Controller.POLLEN_NAME_FR.get(name, name.value) for name in data.pollen_names or []]
    dominant_pollen = (
      Controller.POLLEN_NAME_FR.get(data.dominant_pollen, data.dominant_pollen.value) if data.dominant_pollen else None
    )

    details = {
      Controller.POLLEN_NAME_FR.get(name, name.value): {
        'level': detail.level,
        'severity': Controller.POLLEN_SEVERITY_FR.get(detail.severity, detail.severity.value),
      }
      for name, detail in data.details.items()
    }

    return {
      'pollen_names': pollen_names or None,
      'units': data.units,
      'dominant_pollen': dominant_pollen,
      'details': details,
    }

  def _format_service_data_map(self, data: dict[str, ResponseData | NoneType], *, locale: str | None) -> dict[str, Any]:
    return {
      service: (
        self._localize_pollen_for_prompt(service_data, locale=locale)
        if service == 'pollen' and isinstance(service_data, PollenData)
        else (service_data.model_dump() if isinstance(service_data, BaseModel) else service_data)
      )
      for service, service_data in data.items()
    }

  def _format_prompt_data(self, data: ResponsePayloadModel | ResponseData | NoneType, *, locale: str | None) -> str:
    if data is None:
      return 'Response: Unable to fetch data for the specified location'

    if isinstance(data, PollenData):
      localized_data = self._localize_pollen_for_prompt(data, locale=locale)
      return json.dumps(localized_data, ensure_ascii=False)

    if isinstance(data, BaseModel):
      return data.model_dump_json()

    if isinstance(data, dict):
      keys = list(data.keys())

      if keys and all(key in Controller.SERVICE_NAMES for key in keys):
        service_data_map: dict[str, ResponseData | NoneType] = {
          str(service): service_data
          for service, service_data in data.items()
          if not isinstance(service_data, dict)
        }
        return json.dumps(self._format_service_data_map(service_data_map, locale=locale), ensure_ascii=False)

      payload_by_location: dict[str, Any] = {}

      for location_name, location_data in data.items():
        if isinstance(location_data, dict):
          location_service_map: dict[str, ResponseData | NoneType] = {
            str(service): service_data
            for service, service_data in location_data.items()
            if not isinstance(service_data, dict)
          }
          payload_by_location[location_name] = self._format_service_data_map(location_service_map, locale=locale)
        else:
          payload_by_location[location_name] = location_data

      return json.dumps(payload_by_location, ensure_ascii=False)

    return str(data)

  async def generate_response(
    self,
    user_input: str,
    provider: str,
    location: Location,
    services: list[GetServiceTool.Service],
    data: ResponsePayloadModel,
    temperature_unit: str,
    dateinfo: 'Controller.DateInfo | None',
    locale: str | None = None,
  ) -> 'Controller.Response[ResponsePayloadModel]':
    prompt_data = self._format_prompt_data(data, locale=locale)
    message_language = locale if locale else 'en'

    prompt = (
      f'User Request: {user_input}.\n'
      f'Provider: {provider}.\n'
      f'Services: {", ".join(services)}.\n'
      f'{prompt_data}.\n'
      f'Temperature Unit: {temperature_unit}\n'
      f'User Language: {message_language}\n'
    )

    if dateinfo:
      if dateinfo.start == dateinfo.end:
        prompt += f'Date: {dateinfo.start_date}.'
      else:
        prompt += f'Start Date: {dateinfo.start_date}.\nEnd Date: {dateinfo.end_date}.'

    result = await self.response_agent.generate(prompt)

    self.logger.debug(f'Generated response: {result.response if result else "No response"}')

    return Controller.Response(
      input=user_input,
      services=services,
      provider=provider,
      message=result.response if result else 'No response',
      message_language=message_language,
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
    language: str,
  ) -> 'Controller.AlertResponse[ResponseData | NoneType]':
    prompt_data = self._format_prompt_data(data, locale=language)

    prompt = (
      f'Provider: {provider}.\n'
      f'Provider Response: {prompt_data}.\n'
      f'Temperature Unit: {temperature_unit}\n'
      f'User Language: {language}\n'
    )

    if dateinfo:
      if dateinfo.start == dateinfo.end:
        prompt += f'Date: {dateinfo.start_date}.'
      else:
        prompt += f'Start Date: {dateinfo.start_date}.\nEnd Date: {dateinfo.end_date}.'

    result = await self.alerts_response_agent.generate(prompt)

    self.logger.debug(f'Generated alert response: {result.response if result else "No response"}')

    return Controller.AlertResponse(
      service=service,
      provider=provider,
      message=result.response if result else 'No response',
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
    message_language: str = Field(..., description='Language code used for the generated message')
    data: ResponseDataType | None = Field(..., description='Structured data returned by the provider')
    location: Location = Field(..., description='Location information related to the response')

  class AlertResponse(BaseModel, Generic[ResponseDataType]):
    provider: str = Field(..., description='Name of the data provider')
    service: GetServiceTool.Service = Field(..., description='Service used for generating the response')
    message: str = Field(..., description='Message or explanation related to the response')
    data: ResponseDataType | None = Field(..., description='Structured data returned by the provider')
