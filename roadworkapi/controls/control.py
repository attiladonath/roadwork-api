from __future__ import absolute_import

from roadworkapi.controls.error import Error, ErrorReference, error_codes
from roadworkapi.controls.exceptions import ConstraintException


class Control:
    def _attr_from_request(self, attr, required=False):
        if attr in self._request:
            return self._request[attr]

        if required:
            message = 'Attribute "{}" is required.'.format(attr)
            error = Error(
                message, error_codes.REQUIRED_ATTRIBUTE_MISSING,
                ErrorReference(attr))
            raise ConstraintException(message, 422, error)
        else:
            return None

    def _check_type_dict(self, value, error_reference=''):
        if isinstance(value, dict):
            return value
        else:
            raise self._type_exception('dict', error_reference)

    def _check_type_list_of_strings(self, value, error_reference=''):
        if not isinstance(value, list):
            raise self._type_exception('list', error_reference)

        for i, element in enumerate(value):
            self._check_type_string(
                element, '{}[{}]'.format(error_reference, i))

    def _check_type_int(self, value, error_reference=''):
        try:
            return int(value)
        except ValueError:
            raise self._type_exception('integer', error_reference)

    def _check_type_float(self, value, error_reference=''):
        try:
            return float(value)
        except ValueError:
            raise self._type_exception('float', error_reference)

    def _check_type_string(self, value, error_reference=''):
        if isinstance(value, basestring):
            return value
        else:
            raise self._type_exception('string', error_reference)

    def _check_type_boolean(self, value, error_reference=''):
        if isinstance(value, bool):
            return value
        else:
            raise self._type_exception('boolean', error_reference)

    def _type_exception(self, type, error_reference=''):
        message = 'Wrong type, {} was expected.'.format(type)
        error = Error(
            message, error_codes.WRONG_TYPE, ErrorReference(error_reference))
        raise ConstraintException(message, 422, error)
