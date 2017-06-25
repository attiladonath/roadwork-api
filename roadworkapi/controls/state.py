from __future__ import absolute_import

from sqlalchemy.orm.exc import NoResultFound

from roadworkapi.models.db_models import State as DBState
from roadworkapi.controls import Control
from roadworkapi.controls.error import Error, error_codes
from roadworkapi.controls.exceptions import ValidationException


class State(Control):
    def fetch_all(self):
        return DBState.query.all()

    def fetch_state_by_label(self, label):
        self._check_type_string(label, 'label')
        try:
            return DBState.query.filter_by(label=label).one()
        except NoResultFound:
            message = 'State is not found (label={}).'.format(label)
            error = Error(message, error_codes.STATE_NOT_FOUND)
            raise ValidationException(message, 422, error)
