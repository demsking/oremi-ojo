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
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from injini.core.geo import Geocode
from oremi.skills.weather.models.forecast import Forecast
from oremi.skills.weather.providers.OpenMeteoForecastProvider import OpenMeteoForecastProvider


@pytest.mark.asyncio
async def test_skill_load(skills_manager_en):
  await skills_manager_en.load_skills(['weather'])


@pytest.mark.parametrize('wind_direction, expected_direction', [
  (0.0, 'N'),
  (45.0, 'NE'),
  (90.0, 'E'),
  (135.0, 'SE'),
  (180.0, 'S'),
  (225.0, 'SW'),
  (270.0, 'W'),
  (315.0, 'NW'),
  (360.0, 'N'),
  (400.0, 'NE'),
])
def test_determine_direction(wind_direction, expected_direction):
  result = OpenMeteoForecastProvider.get_wind_direction(wind_direction)

  assert result == expected_direction


@pytest.mark.asyncio
@pytest.mark.parametrize('fixture', [
  ('us', 25, 'USAQI', 'USAQI-0-50'),
  ('us', 51, 'USAQI', 'USAQI-51-100'),
  ('us', 102, 'USAQI', 'USAQI-101-150'),
  ('us', 160, 'USAQI', 'USAQI-151-200'),
  ('us', 300, 'USAQI', 'USAQI-201-300'),
  ('eu', 5, 'EAQI', 'EAQI-0-20'),
  ('eu', 25, 'EAQI', 'EAQI-20-40'),
  ('eu', 41, 'EAQI', 'EAQI-40-60'),
  ('eu', 65, 'EAQI', 'EAQI-60-80'),
  ('eu', 100, 'EAQI', 'EAQI-80-100'),
])
async def test_exec_air_quality(fixture, weather_skill, create_args, air_quality_data, user_input_location_cm_mock, user_input_location_us_mock):
  type, aqi, unit, prefix = fixture
  args = create_args('air-quality', 'What is the air quality today?')
  skill = await weather_skill
  FAKE_DATE = datetime.datetime(2023, 5, 27, 17, 29, 0, 0)

  with patch('datetime.datetime', wraps=datetime.datetime) as datetime_mock:
    datetime_mock.now.return_value = FAKE_DATE
    hourly_key = 'us_aqi' if type == 'us' else 'european_aqi'
    user_input_location = user_input_location_us_mock if type == 'us' else user_input_location_cm_mock
    skill.get_user_input_location_with_default = MagicMock(return_value=user_input_location)

    skill.air_quality_client.get = Mock()
    skill.air_quality_client.get.return_value.json = Mock(
      side_effect=lambda: air_quality_data,
    )

    air_quality_data['hourly'][hourly_key] = [aqi for x in range(0, 30)]

    await skill.exec_air_quality(args)

    skill.send_response.assert_called_once()
    assert skill.send_response.call_args[0][0] == args
    assert skill.send_response.call_args[0][1] == {
      'value': aqi,
      'unit': unit,
    }

    args.feature.message.__getitem__.assert_called_with(prefix)
    skill.air_quality_client.get.assert_called_with('/v1/air-quality', params={
      'latitude': user_input_location[1].latitude,
      'longitude': user_input_location[1].longitude,
      'hourly': 'european_aqi,us_aqi',
      'start_date': FAKE_DATE.date().isoformat(),
      'end_date': FAKE_DATE.date().isoformat(),
    })


@pytest.mark.asyncio
@pytest.mark.parametrize('fixture', [
  ('us', 25, 'USAQI', 'USAQI-0-50'),
  ('us', 51, 'USAQI', 'USAQI-51-100'),
  ('us', 102, 'USAQI', 'USAQI-101-150'),
  ('us', 160, 'USAQI', 'USAQI-151-200'),
  ('us', 300, 'USAQI', 'USAQI-201-300'),
  ('eu', 5, 'EAQI', 'EAQI-0-20'),
  ('eu', 25, 'EAQI', 'EAQI-20-40'),
  ('eu', 41, 'EAQI', 'EAQI-40-60'),
  ('eu', 65, 'EAQI', 'EAQI-60-80'),
  ('eu', 100, 'EAQI', 'EAQI-80-100'),
])
async def test_exec_pollen(fixture, weather_skill, create_args, rnsa_data, user_input_location_cm_mock, user_input_location_us_mock):
  type, aqi, unit, prefix = fixture
  args = create_args('air-quality', 'What is the air quality today?')
  skill = await weather_skill
  FAKE_DATE = datetime.datetime(2023, 5, 27, 17, 29, 0, 0)

  with patch('datetime.datetime', wraps=datetime.datetime) as datetime_mock:
    datetime_mock.now.return_value = FAKE_DATE
    user_input_location = user_input_location_us_mock if type == 'us' else user_input_location_cm_mock
    skill.get_user_input_location_with_default = MagicMock(return_value=user_input_location)

    skill.air_quality_client.get = Mock()
    skill.air_quality_client.get.return_value.json = Mock(
      side_effect=lambda: rnsa_data,
    )

    await skill.exec_air_quality(args)

    skill.send_response.assert_called_once()
    assert skill.send_response.call_args[0][0] == args
    assert skill.send_response.call_args[0][1] == {
      'value': aqi,
      'unit': unit,
    }

    args.feature.message.__getitem__.assert_called_with(prefix)
    skill.air_quality_client.get.assert_called_with('/v1/air-quality', params={
      'latitude': user_input_location[1].latitude,
      'longitude': user_input_location[1].longitude,
      'hourly': 'european_aqi,us_aqi',
      'start_date': FAKE_DATE.date().isoformat(),
      'end_date': FAKE_DATE.date().isoformat(),
    })


@pytest.mark.asyncio
async def test_get_forecast_params(weather_skill, create_args, user_input_location_cm_mock, forcast_data, forecast_params):
  skill = await weather_skill
  args = create_args('local', 'What''s the current weather?')
  FAKE_DATE = datetime.datetime(2023, 5, 28, 11, 29, 0, 0)

  with patch('datetime.datetime', wraps=datetime.datetime) as datetime_mock:
    datetime_mock.now.return_value = FAKE_DATE

    patch.object(Geocode, 'find', Mock(return_value=user_input_location_cm_mock))
    skill.open_meteo_client.get = Mock()
    skill.open_meteo_client.get.return_value.json = Mock(
      side_effect=lambda: forcast_data,
    )

    forecast, params = skill.get_forecast_params(args)

    assert isinstance(forecast, Forecast)
    assert params == forecast_params


@pytest.mark.asyncio
async def test_exec_humidity_level(weather_skill, create_args, forcast_data, forecast_params):
  skill = await weather_skill
  args = create_args('humidity', 'What is the humidity level?')
  forecast = Forecast(**forcast_data)
  skill.get_forecast_params = Mock(return_value=(forecast, forecast_params))

  await skill.exec_humidity_level(args)

  skill.send_response.assert_called_once_with(args, forecast_params)


@pytest.mark.asyncio
async def test_exec_forecast(weather_skill, create_args, forcast_data, forecast_params):
  skill = await weather_skill
  args = create_args('local', 'What''s the current weather?')
  forecast = Forecast(**forcast_data)
  skill.get_forecast_params = Mock(return_value=(forecast, forecast_params))

  await skill.exec_forecast(args)

  skill.get_forecast_params.assert_called_with(args)
  args.feature.message.__getitem__.assert_called_with('weather_codes_0')


@pytest.mark.asyncio
async def test_exec_sunset(weather_skill, create_args, forcast_data, forecast_params):
  skill = await weather_skill
  args = create_args('sunset', 'What time does the sun set today?')
  forecast = Forecast(**forcast_data)
  skill.get_forecast_params = Mock(return_value=(forecast, forecast_params))

  await skill.exec_sunset(args)

  skill.send_response.assert_called_once_with(args, forecast_params)


@pytest.mark.asyncio
async def test_exec_sunrise(weather_skill, create_args):
  skill = await weather_skill
  args = create_args('sunrise', 'What time does the sun rise today?')
  exec_sunset_mock = Mock()

  async def exec_sunset(*args, **kwargs):
    exec_sunset_mock(*args, **kwargs)

  skill.exec_sunset = exec_sunset

  await skill.exec_sunrise(args)

  exec_sunset_mock.assert_called_with(args)


@pytest.mark.asyncio
@pytest.mark.parametrize('fixture', [
  (1, 'yes'),
  (0, 'no'),
])
async def test_exec_is_day(fixture, weather_skill, create_args, forcast_data, forecast_params):
  is_day_value, message_key = fixture

  skill = await weather_skill
  args = create_args('is-day', 'Is it daytime?')
  forecast = Forecast(**forcast_data)
  skill.get_forecast_params = Mock(return_value=(forecast, forecast_params))

  forecast.current_weather.is_day = is_day_value

  await skill.exec_is_day(args)

  skill.get_forecast_params.assert_called_with(args)
  args.feature.message.__getitem__.assert_called_with(message_key)


@pytest.mark.asyncio
@pytest.mark.parametrize('fixture', [
  (0, 'yes'),
  (1, 'no'),
])
async def test_exec_is_night(fixture, weather_skill, create_args, forcast_data, forecast_params):
  is_day_value, message_key = fixture

  skill = await weather_skill
  args = create_args('is-night', 'Is it nighttime?')
  forecast = Forecast(**forcast_data)
  skill.get_forecast_params = Mock(return_value=(forecast, forecast_params))

  forecast.current_weather.is_day = is_day_value

  await skill.exec_is_night(args)

  skill.get_forecast_params.assert_called_with(args)
  args.feature.message.__getitem__.assert_called_with(message_key)
