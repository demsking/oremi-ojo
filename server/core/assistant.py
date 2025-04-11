# Copyright 2025 Sébastien Demanou. All Rights Reserved.
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

import httpx
from ollama import AsyncClient
from ollama import GenerateResponse
from ollama import Message
from ollama import Options
from ollama import ResponseError
from ollama import Tool


class Assistant:
  def __init__(
    self,
    *,
    model: str,
    ollama_baseurl: str,
    logger: logging.Logger,
  ) -> None:
    self.logger = logger
    self.model = model
    self.ollama_baseurl = ollama_baseurl
    self.client = AsyncClient(
      host=ollama_baseurl,
      timeout=httpx.Timeout(None),  # no timeout
    )

  def create_agent(self, system: str | None) -> 'Agent':
    return Agent(
      model=self.model,
      ollama_baseurl=str(self.ollama_baseurl),
      logger=self.logger,
      system=system,
    )

  def create_tools_agent(self, tools: list[Tool], system: str | None = None) -> 'ToolsAgent':
    return ToolsAgent(model=self.model, ollama_baseurl=self.ollama_baseurl, logger=self.logger, system=system, tools=tools)

  async def load_model(self) -> None:
    self.logger.info(f'Pulling model {self.model}...')
    await self.client.pull(self.model, stream=False)

    self.logger.info(f'Loading model {self.model}...')
    await self.client.generate(
      model=self.model,
      keep_alive=-1,  # any negative number which will keep the model loaded in memory
    )


class Agent:
  def __init__(
    self,
    *,
    model: str,
    ollama_baseurl: str,
    logger: logging.Logger,
    system: str | None = None,
  ) -> None:
    self.logger = logger
    self.model = model
    self.system = system
    self.client = AsyncClient(
      host=ollama_baseurl,
      timeout=httpx.Timeout(None),  # no timeout
    )

  async def generate(
    self,
    prompt: str,
    options: Options | None = None,
  ) -> GenerateResponse | None:
    self.logger.debug(f'Generating with prompt:\n{prompt}')

    try:
      return await self.client.generate(
        model=self.model,
        prompt=prompt,
        system=self.system or '',
        stream=False,
        options=options,
      )
    except ResponseError as error:
      self.logger.error(f'Ollama Error: {error.error}')
      return None


class ToolsAgent:
  def __init__(
    self,
    *,
    model: str,
    ollama_baseurl: str,
    logger: logging.Logger,
    tools: list[Tool],
    system: str | None = None,
  ) -> None:
    self.logger = logger
    self.client = AsyncClient(
      host=ollama_baseurl,
      timeout=httpx.Timeout(None),  # no timeout
    )

    self.model = model
    self.system = system
    self.tools = tools

  async def query(
    self,
    input: str,
    tools: list[Tool] | None = None,
  ) -> Message.ToolCall.Function | None:
    messages: list[Message] = []

    if self.system:
      messages.append(Message(role='system', content=self.system))

    messages.append(Message(role='user', content=input))
    messages_dump = [message.model_dump() for message in messages]

    self.logger.debug(f'Querying with messages {messages}')

    response = await self.client.chat(
      self.model,
      messages=messages_dump,
      tools=tools or self.tools,
      stream=False,
    )

    if response.message.tool_calls:
      for tool in response.message.tool_calls:
        return tool.function

    return None
