# Copyright 2026 Sébastien Demanou. All Rights Reserved.
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
from typing import Generic
from typing import TypeVar

from pydantic import AliasChoices
from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import Field

from weather.core.controller import ResponsePayloadModel
from weather.core.geo import Location
from weather.tools.service_tool import GetServiceTool


class ProcessRequest(BaseModel):
  """Request model for NLP processing."""

  model_config = ConfigDict(str_strip_whitespace=True)

  message: str = Field(
    min_length=1,
    max_length=8000,
    validation_alias=AliasChoices('message', 'text'),
    description='Input text to be processed by the NLP system. Must be between 1 and 8000 characters.',
    examples=[
      "What's the weather like in Lagos?",
      'Quel temps fait-il à Paris ?',
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
  )

  context: dict[str, Any] = Field(
    default_factory=dict,
    description=(
      'Optional contextual information for the request. Used to maintain '
      'conversation state or provide additional processing context.\n\n'
      'Context carries structured data needed such as an IANA timezone, '
      'coordinates or temperature unit.'
    ),
    examples=[
      {
        'timezone': 'Africa/Lagos',
      },
      {
        'timezone': 'Africa/Douala',
        'latitude': 48.8566,
        'longitude': 2.3522,
        'temperature_unit': 'celsius',
      },
    ],
  )


ResponseDataType = TypeVar('ResponseDataType', bound=BaseModel | ResponsePayloadModel | NoneType)


class ProcessResponse(BaseModel, Generic[ResponseDataType]):
  """Response model for NLP processing results."""

  ok: bool = Field(default=True, description='Indicates whether the processing was successful.')  # pylint: disable=invalid-name
  input: str = Field(description='Original input text that was processed.')
  services: list[GetServiceTool.Service] = Field(..., description='List of services used for generating the response')
  message: str = Field(description='Human-readable response message containing the processing result or error details.')
  data: ResponseDataType | None = Field(
    default=None,
    description='Additional structured data from the processing. Content varies based on the service and request type.',
  )
  location: Location = Field(..., description='Location information related to the response')

  confidence: float = Field(
    ge=0, le=1, description='Confidence score for the response, ranging from 0.0 (lowest) to 1.0 (highest).'
  )
