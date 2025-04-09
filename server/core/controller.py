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
from typing import Generic
from typing import TypeVar

from ollama import Tool
from pydantic import BaseModel
from pydantic import Field

from ..core.assistant import Assistant
from ..core.geo import Location
from ..tools.date_tool import GetDateTool
from ..tools.date_tool import Period
from ..tools.location_tool import GetLocationTool
from ..tools.service_tool import GetServiceTool

ResponseData = TypeVar('ResponseData', bound=BaseModel)


class Controller:
  def __init__(
    self,
    assistant: Assistant,
    logger: logging.Logger,
  ):
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
    self, user_input: str, provider: str, location: Location, data: ResponseData, dateinfo: 'Controller.DateInfo | None'
  ) -> 'Controller.Response':
    prompt = f'User Request: {user_input}.\nProvider: {provider}.\n{data}.\n'

    if dateinfo:
      if dateinfo.start == dateinfo.end:
        prompt += f'Date: {dateinfo.start_date}.'
      else:
        prompt += f'Start Date: {dateinfo.start_date}.\nEnd Date: {dateinfo.end_date}.'

    result = await self.response_agent.generate(prompt)

    return Controller.Response(
      input=user_input,
      provider=provider,
      message=result.response if result else 'No response',
      location=location,
      data=data,
    )

  async def get_date(self, user_input: str, timezone: str):
    tool, start, end = await self.date_agent.get_date(user_input, timezone=timezone)
    start_date = start.date().isoformat()
    end_date = end.date().isoformat()
    period = GetDateTool.period_map[tool.name]

    return Controller.DateInfo(
      tool=tool,
      period=period,
      start=start,
      start_date=start_date,
      end=end,
      end_date=end_date,
      timezone=timezone,
    )

  class DateInfo(BaseModel):
    tool: Tool.Function
    period: Period
    start: datetime
    start_date: str
    end: datetime
    end_date: str
    timezone: str

  class Response(BaseModel, Generic[ResponseData]):
    provider: str = Field(..., description='Name of the data provider')
    input: str = Field(..., description='User input that triggered the response')
    message: str = Field(..., description='Message or explanation related to the response')
    data: ResponseData = Field(..., description='Structured data returned by the provider')
    location: Location = Field(..., description='Location information related to the response')
