from __future__ import absolute_import

import flask


def data_response(data, pagination_data=None):
    response = {'data': data}
    if pagination_data:
        response.update({'pagination': pagination_data})
    return json_response(response)


def error_response(error):
    response = {'error': {
        'message': error.message,
        'code': error.code,
        'reference': str(error.reference)
    }}
    return json_response(response)


def json_response(response):
    return flask.jsonify(response)
