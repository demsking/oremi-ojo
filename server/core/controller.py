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
from typing import Generic
from typing import TypeVar

from pydantic import BaseModel

from ..core.assistant import Assistant
from ..core.geo import Location
from ..tools.date_tool import GetDateTool
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

    self.agent = assistant.create_agent(
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
        'If the user asks for weather information about a future or past day, inform them that you can only provide information for the current day.\n'
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
    self, user_input: str, provider: str, location: Location, data: ResponseData
  ) -> 'Controller.Response':
    result = await self.agent.generate(prompt=(f'User Request: {user_input}.\nProvider: {provider}.\n{data}.\n'))

    return Controller.Response(
      provider=provider,
      message=result.response if result else 'No response',
      location=location,
      data=data,
    )

  class Response(BaseModel, Generic[ResponseData]):
    provider: str
    message: str
    data: ResponseData
    location: Location
