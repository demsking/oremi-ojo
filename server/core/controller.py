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
import logging
from datetime import datetime
from types import NoneType
from typing import Any
from typing import Generic
from typing import Literal
from typing import TypeVar

from pydantic import BaseModel
from pydantic import Field

from ..core.assistant import Assistant
from ..core.geo import Location
from ..tools.date_tool import GetDateTool
from ..tools.date_tool import Period
from ..tools.location_tool import GetLocationTool
from ..tools.service_tool import GetServiceTool

ResponseData = TypeVar('ResponseData', bound=BaseModel | NoneType)
WeatherService = Literal['air-quality', 'weather', 'pollen']


class Controller:
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

  async def generate_response(
    self,
    user_input: str,
    provider: str,
    location: Location,
    service: WeatherService,
    data: Any | None,
    temperature_unit: str,
    dateinfo: 'Controller.DateInfo | None',
  ) -> 'Controller.Response[Any]':
    prompt = (
      f'User Request: {user_input}.\n'
      f'Provider: {provider}.\n'
      f'{data or "Response: Unable to fetch data for the specified location"}.\n'
      f'Temperature Unit: {temperature_unit}\n'
    )

    if dateinfo:
      if dateinfo.start == dateinfo.end:
        prompt += f'Date: {dateinfo.start_date}.'
      else:
        prompt += f'Start Date: {dateinfo.start_date}.\nEnd Date: {dateinfo.end_date}.'

    result = await self.response_agent.generate(prompt)

    return Controller.Response(
      input=user_input,
      service=service,
      provider=provider,
      message=result.response if result else 'No response',
      location=location,
      data=data,
    )

  async def generate_alert_response(
    self,
    provider: str,
    service: WeatherService,
    data: BaseModel | None,
    temperature_unit: str,
    dateinfo: 'Controller.DateInfo | None',
    language: str,
  ) -> 'Controller.AlertResponse[Any]':
    prompt = (
      f'Provider: {provider}.\n'
      f'{data or "Response: Unable to fetch data for the specified location"}.\n'
      f'Temperature Unit: {temperature_unit}\n'
      f'User Language: {language}'
    )

    if dateinfo:
      if dateinfo.start == dateinfo.end:
        prompt += f'Date: {dateinfo.start_date}.'
      else:
        prompt += f'Start Date: {dateinfo.start_date}.\nEnd Date: {dateinfo.end_date}.'

    result = await self.alerts_response_agent.generate(prompt)

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

  class Response(BaseModel, Generic[ResponseData]):
    provider: str = Field(..., description='Name of the data provider')
    input: str = Field(..., description='User input that triggered the response')
    service: WeatherService = Field(..., description='Service used for generating the response')
    message: str = Field(..., description='Message or explanation related to the response')
    data: ResponseData | None = Field(..., description='Structured data returned by the provider')
    location: Location = Field(..., description='Location information related to the response')

  class AlertResponse(BaseModel, Generic[ResponseData]):
    provider: str = Field(..., description='Name of the data provider')
    service: WeatherService = Field(..., description='Service used for generating the response')
    message: str = Field(..., description='Message or explanation related to the response')
    data: ResponseData | None = Field(..., description='Structured data returned by the provider')
