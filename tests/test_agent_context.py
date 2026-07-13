from ojo.api.agent import _dedupe_locations
from ojo.core.geo import Location


def _location(name: str, lat: float, lon: float) -> Location:
  return Location.model_validate(
    {
      'type': 'city',
      'name': name,
      'boundingbox': [lat, lat, lon, lon],
      'lat': lat,
      'lon': lon,
      'addresstype': 'city',
      'display_name': f'{name}, France',
      'address': {'country': 'France', 'country_code': 'fr'},
    }
  )


def test_dedupe_locations_collapses_near_duplicate_results():
  locations = [
    _location('Paris', 48.8566, 2.3522),
    _location('Paris', 48.8589, 2.3470),
    _location('Lyon', 45.7640, 4.8357),
  ]

  deduped = _dedupe_locations(locations)

  assert [location.name for location in deduped] == ['Paris', 'Lyon']
