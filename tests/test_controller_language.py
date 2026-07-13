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
from dataclasses import dataclass

from ojo.core.controller import Controller
from ojo.core.geo import Location
from ojo.models.forecast import ForecastData


@dataclass
class FakeGenerationResult:
  response: str


class FakeAgent:
  def __init__(self, response: str | None = None):
    self.response = response
    self.prompts: list[str] = []

  async def generate(self, prompt: str):
    self.prompts.append(prompt)
    return FakeGenerationResult(self.response or '')


class FakeAssistant:
  def __init__(self):
    self.response_agent = FakeAgent('Il fera beau.')
    self.language_agent = FakeAgent('fr')
    self.tools_agent = FakeAgent()

  def create_agent(self, system: str):
    if 'Detect the language' in system:
      return self.language_agent

    return self.response_agent

  def create_tools_agent(self, tools, system=None):
    return self.tools_agent


def _make_location() -> Location:
  return Location.model_validate(
    {
      'type': 'city',
      'name': 'Paris',
      'boundingbox': [48.80, 48.90, 2.25, 2.40],
      'lat': 48.8566,
      'lon': 2.3522,
      'addresstype': 'city',
      'display_name': 'Paris, France',
      'address': {
        'country': 'France',
        'country_code': 'fr',
      },
    }
  )


def test_language_instruction_for_french_requests():
  instruction = Controller._language_instruction('fr')

  assert instruction == 'The user request is written in French. Reply in French.'


def test_language_instruction_defaults_to_english():
  instruction = Controller._language_instruction('')

  assert instruction == 'The user request is written in English. Reply in English.'


async def test_generate_response_uses_request_language():
  assistant = FakeAssistant()
  controller = Controller(assistant)  # type: ignore[arg-type]

  response = await controller.generate_response(
    user_input='Quelle est la météo à Paris ?',
    provider='Open-Meteo',
    location=_make_location(),
    services=['weather'],
    data=None,
    temperature_unit='celsius',
    dateinfo=None,
  )

  assert response.message == 'Il fera beau.'
  assert 'The user request is written in French. Reply in French.' in assistant.response_agent.prompts[0]


async def test_generate_response_uses_provided_language_without_detection():
  assistant = FakeAssistant()
  controller = Controller(assistant)  # type: ignore[arg-type]

  response = await controller.generate_response(
    user_input='Quelle est la météo à Paris ?',
    provider='Open-Meteo',
    location=_make_location(),
    services=['weather'],
    data=None,
    temperature_unit='celsius',
    dateinfo=None,
    language='fr',
  )

  assert response.message == 'Il fera beau.'
  assert assistant.language_agent.prompts == []
  assert 'The user request is written in French. Reply in French.' in assistant.response_agent.prompts[0]


def test_weather_prompt_keeps_only_relevant_available_fields():
  assistant = FakeAssistant()
  controller = Controller(assistant)  # type: ignore[arg-type]

  prompt_data = controller._format_prompt_data(
    {
      'weather': ForecastData(
        temperature='34.81949996948242°C',
        humidity='20.0%',
        wind_speed='14.399999618530273 km/h',
        sunrise='06:01:25',
        sunset='21:51:24',
      )
    },
    user_input='Quel temps fait-il à Paris ?',
  )

  assert '34.8°C' in prompt_data
  assert '14.4 km/h' in prompt_data
  assert 'sunrise' not in prompt_data
  assert 'sunset' not in prompt_data
  assert 'air-quality' not in prompt_data


def test_weather_prompt_keeps_solar_field_only_when_requested():
  assistant = FakeAssistant()
  controller = Controller(assistant)  # type: ignore[arg-type]

  prompt_data = controller._format_prompt_data(
    {
      'weather': ForecastData(
        temperature='34.8°C',
        humidity='20%',
        wind_speed='14.4 km/h',
        sunrise='06:01:25',
        sunset='21:51:24',
      )
    },
    user_input='À quelle heure le soleil se couche à Paris ?',
  )

  assert 'sunset' in prompt_data
  assert '21:51:24' in prompt_data
  assert 'temperature' not in prompt_data
  assert 'sunrise' not in prompt_data
