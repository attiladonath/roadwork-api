from __future__ import absolute_import

import re

from roadworkapi.models.db_models import Streetview as DBStreetview
from roadworkapi.controls import Control
from roadworkapi.controls.error import Error, error_codes
from roadworkapi.controls.exceptions import ValidationException
from roadworkapi.controls.utils import google_domains


class Streetview(Control):
    VALID_STREETVIEW_URL_PATTERN = (
        '^https://www\.google\.({})/maps([^\?])*/@([A-Za-z0-9,\.])*/data=.*$'
        .format('|'.join(google_domains).replace('.', '\.')))

    def build_from_request(self, streetview_url):
        self._check_type_string(streetview_url)
        if not self.is_valid_streetview_url(streetview_url):
            message = (
                'URL is not a valid Google Street View URL "{}".'
                .format(streetview_url))
            error = Error(message, error_codes.INVALID_STREETVIEW_URL)
            raise ValidationException(message, 422, error)

        return DBStreetview(streetview_url)

    def is_valid_streetview_url(self, url):
        return re.match(self.VALID_STREETVIEW_URL_PATTERN, url)
