from __future__ import absolute_import

from roadworkapi.models.db_models import Coordinates as DBCoordinates
from roadworkapi.controls import Control


class Coordinates(Control):
    def build_from_request(self, coordinates):
        self._request = self._check_type_dict(coordinates)
        longitude = self._attr_from_request('longitude', required=True)
        latitude = self._attr_from_request('latitude', required=True)
        return DBCoordinates(
            self._check_type_float(longitude, 'longitude'),
            self._check_type_float(latitude, 'latitude'))
