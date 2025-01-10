# Copyright 2024 Sébastien Demanou. All Rights Reserved.
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
import datetime
from unittest.mock import AsyncMock
from unittest.mock import MagicMock

import pytest

from oremi.skills.weather import WeatherSkill


@pytest.fixture
async def weather_skill(skills_manager_en, user_input_location_cm_mock):
  skills_manager_en.init_skills(['weather'])
  await skills_manager_en.load_skills(['weather'])
  skill: WeatherSkill = skills_manager_en.skills['oremi.skills.weather']
  skill.get_user_input_location_with_default = AsyncMock(return_value=user_input_location_cm_mock)
  skill.send_response = MagicMock()
  return skill


@pytest.fixture
def create_args(get_exec_args_en):
  def create_args(feature_name, input_text):
    args = get_exec_args_en('weather', feature_name, input_text)
    args.skill.dictionary = {
      'N': 'North',
      'NNE': 'North-Northeast',
      'NE': 'Northeast',
      'ENE': 'East-Northeast',
      'E': 'East',
      'ESE': 'East-Southeast',
      'SE': 'Southeast',
      'SSE': 'South-Southeast',
      'S': 'South',
      'SSW': 'South-Southwest',
      'SW': 'Southwest',
      'WSW': 'West-Southwest',
      'W': 'West',
      'WNW': 'West-Northwest',
      'NW': 'Northwest',
      'NNW': 'North-Northwest'
    }
    return args
  return create_args


@pytest.fixture
def air_quality_data():
  return {
    'latitude': 48.85,
    'longitude': 2.5499992,
    'generationtime_ms': 0.5059242248535156,
    'utc_offset_seconds': 0,
    'timezone': 'GMT',
    'timezone_abbreviation': 'GMT',
    'hourly_units': {
      'time': 'iso8601',
      'european_aqi': 'EAQI',
      'us_aqi': 'USAQI'
    },
    'hourly': {
      'time': [
        '2023-05-27T00:00',
        '2023-05-27T01:00',
        '2023-05-27T02:00',
        '2023-05-27T03:00',
        '2023-05-27T04:00',
        '2023-05-27T05:00',
        '2023-05-27T06:00',
        '2023-05-27T07:00',
        '2023-05-27T08:00',
        '2023-05-27T09:00',
        '2023-05-27T10:00',
        '2023-05-27T11:00',
        '2023-05-27T12:00',
        '2023-05-27T13:00',
        '2023-05-27T14:00',
        '2023-05-27T15:00',
        '2023-05-27T16:00',
        '2023-05-27T17:00',
        '2023-05-27T18:00',
        '2023-05-27T19:00',
        '2023-05-27T20:00',
        '2023-05-27T21:00',
        '2023-05-27T22:00',
        '2023-05-27T23:00'
      ],
      'european_aqi': [
        28,
        27,
        27,
        27,
        27,
        27,
        26,
        26,
        26,
        29,
        32,
        37,
        39,
        41,
        42,
        43,
        42,
        41,
        37,
        32,
        27,
        26,
        26,
        24
      ],
      'us_aqi': [
        53,
        54,
        53,
        53,
        53,
        53,
        52,
        52,
        52,
        51,
        51,
        51,
        50,
        50,
        49,
        49,
        49,
        48,
        48,
        47,
        46,
        46,
        45,
        44
      ]
    }
  }


@pytest.fixture
def forcast_data():
  return {
    'latitude': 48.84,
    'longitude': 2.56,
    'generationtime_ms': 1.0570287704467773,
    'utc_offset_seconds': 7200,
    'timezone': 'Europe/Paris',
    'timezone_abbreviation': 'CEST',
    'elevation': 101,
    'current_weather': {
      'temperature': 17.5,
      'windspeed': 10.2,
      'winddirection': 23,
      'weathercode': 0,
      'is_day': 1,
      'time': '2023-05-28T10:00'
    },
    'hourly_units': {
      'time': 'iso8601',
      'temperature_2m': '°C',
      'relativehumidity_2m': '%',
      'windspeed_10m': 'km/h'
    },
    'hourly': {
      'time': [
        '2023-05-28T00:00',
        '2023-05-28T01:00',
        '2023-05-28T02:00',
        '2023-05-28T03:00',
        '2023-05-28T04:00',
        '2023-05-28T05:00',
        '2023-05-28T06:00',
        '2023-05-28T07:00',
        '2023-05-28T08:00',
        '2023-05-28T09:00',
        '2023-05-28T10:00',
        '2023-05-28T11:00',
        '2023-05-28T12:00',
        '2023-05-28T13:00',
        '2023-05-28T14:00',
        '2023-05-28T15:00',
        '2023-05-28T16:00',
        '2023-05-28T17:00',
        '2023-05-28T18:00',
        '2023-05-28T19:00',
        '2023-05-28T20:00',
        '2023-05-28T21:00',
        '2023-05-28T22:00',
        '2023-05-28T23:00'
      ],
      'temperature_2m': [
        17.4,
        16.4,
        15.5,
        14.6,
        13.8,
        12.8,
        12.5,
        12.5,
        13.3,
        15.1,
        17.5,
        19.7,
        21.5,
        23.4,
        24.5,
        25.2,
        25.7,
        25.7,
        25.7,
        24.9,
        23.8,
        22.4,
        20.6,
        18.8
      ],
      'relativehumidity_2m': [
        68,
        68,
        66,
        69,
        72,
        76,
        77,
        78,
        77,
        70,
        62,
        56,
        53,
        45,
        39,
        36,
        34,
        41,
        35,
        41,
        42,
        46,
        48,
        59
      ],
      'windspeed_10m': [
        8.7,
        9.1,
        9,
        10,
        9.2,
        7.4,
        5.8,
        5.9,
        7.4,
        8.3,
        10.2,
        11.8,
        12.3,
        14.5,
        15.5,
        16,
        15.5,
        15.1,
        16.3,
        17.2,
        16.1,
        13.8,
        11.9,
        10.8
      ]
    },
    'daily_units': {
      'time': 'iso8601',
      'sunrise': 'iso8601',
      'sunset': 'iso8601'
    },
    'daily': {
      'time': [
        '2023-05-28'
      ],
      'sunrise': [
        '2023-05-28T05:52'
      ],
      'sunset': [
        '2023-05-28T21:41'
      ]
    }
  }


@pytest.fixture
def rnsa_data():
  return {
    'countyName': 'Val-de-Marne',
    'countyNumber': '94',
    'risks': [
      {
        'pollenName': 'Urticac\u00e9es',
        'level': 1
      },
      {
        'pollenName': 'Tilleul',
        'level': 0
      },
      {
        'pollenName': 'Saule',
        'level': 0
      },
      {
        'pollenName': 'Platane',
        'level': 0
      },
      {
        'pollenName': 'Plantain',
        'level': 1
      },
      {
        'pollenName': 'Peuplier',
        'level': 0
      },
      {
        'pollenName': 'Oseille',
        'level': 1
      },
      {
        'pollenName': 'Olivier',
        'level': 0
      },
      {
        'pollenName': 'Noisetier',
        'level': 0
      },
      {
        'pollenName': 'Gramin\u00e9es',
        'level': 3
      },
      {
        'pollenName': 'Fr\u00eane',
        'level': 0
      },
      {
        'pollenName': 'Cupressac\u00e9es',
        'level': 0
      },
      {
        'pollenName': 'Ch\u00eane',
        'level': 0
      },
      {
        'pollenName': 'Ch\u00e2taignier',
        'level': 0
      },
      {
        'pollenName': 'Charme',
        'level': 0
      },
      {
        'pollenName': 'Bouleau',
        'level': 0
      },
      {
        'pollenName': 'Aulne',
        'level': 0
      },
      {
        'pollenName': 'Armoise',
        'level': 0
      },
      {
        'pollenName': 'Ambroisies',
        'level': 0
      }
    ],
    'riskLevel': 3,
  }


@pytest.fixture
def forecast_params():
  return {
    'humidity': 56,
    'humidity_unit': '%',
    'place': 'Douala',
    'sunrise_hour': 5,
    'sunrise_minute': 52,
    'sunrise_second': 0,
    'sunrise_day': 28,
    'sunrise_month': 5,
    'sunrise_year': 2023,
    'sunrise_raw': datetime.datetime(2023, 5, 28, 5, 52),
    'sunset_hour': 21,
    'sunset_minute': 41,
    'sunset_second': 0,
    'sunset_day': 28,
    'sunset_month': 5,
    'sunset_year': 2023,
    'sunset_raw': datetime.datetime(2023, 5, 28, 21, 41),
    'temperature': 19.7,
    'temperature_unit': '°C',
    'wind_direction': 'North-Northeast',
    'wind_speed': 11.8,
    'wind_speed_unit': 'km/h',
  }
