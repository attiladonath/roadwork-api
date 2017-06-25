from __future__ import absolute_import

from roadworkapi.models.db_models import Description as DBDescription
from roadworkapi.controls import Control


class Description(Control):
    def build_from_request(self, description):
        self._check_type_string(description)
        return DBDescription(description)
