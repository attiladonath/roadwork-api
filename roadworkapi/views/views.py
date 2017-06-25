from __future__ import absolute_import

import os
import flask

from roadworkapi import app
from roadworkapi.views.response_formatters import (
    data_response, error_response)
from roadworkapi.views.model_formatters import (
    IssueFormatter, IssueVersionFormatter, StateFormatter, TagFormatter)
from roadworkapi.controls import (Issue, IssueVersion, State, Tag)
from roadworkapi.controls.exceptions import PublicException
from roadworkapi.controls.error import error_codes


@app.route('/', methods=['GET'])
def index():
    return "It's working.", 200  # OK


@app.route('/swagger.yaml', methods=['GET'])
def swagger():
    swagger_file = os.path.join(os.getcwd(), 'swagger', 'swagger.yaml')
    return flask.send_file(swagger_file, mimetype='text/yaml')


@app.route('/issues', methods=['GET'])
def list_issues():
    try:
        issues, pagination = Issue().query_paged_by_args(flask.request.args)
        formatted_issues = [IssueFormatter(i).dict for i in issues]
        return data_response(formatted_issues, pagination)
    except PublicException as e:
        e.error.reference.place = 'QUERY'
        return error_response(e.error), e.response_code


@app.route('/issues/<int:id>/versions', methods=['GET'])
def list_issue_versions(id):
    versions = IssueVersion().fetch_all_for_issue_by_id(id)
    formatted_versions = [IssueVersionFormatter(v).dict for v in versions]
    return data_response(formatted_versions)


@app.route('/issues', methods=['POST'])
def add_issue():
    try:
        request = flask.request.get_json()
        issue = Issue().create_from_request(request)
        formatted_issue = IssueFormatter(issue).dict
        return data_response(formatted_issue), 201
    except PublicException as e:
        e.error.reference.place = 'BODY'
        return error_response(e.error), e.response_code


@app.route('/issues/<int:id>/versions', methods=['POST'])
def add_issue_version(id=None):
        try:
            request = flask.request.get_json()
            issue_version = (
                IssueVersion()
                .create_from_request_for_issue_by_id(request, id))
            formatted_issue_version = IssueVersionFormatter(issue_version).dict
            return data_response(formatted_issue_version), 201
        except PublicException as e:
            if error_codes.LATEST_ISSUE_VERSION_NOT_FOUND == e.error.code:
                e.error.reference.place = 'PATH'
            else:
                e.error.reference.place = 'BODY'
            return error_response(e.error), e.response_code


@app.route('/issues/<int:id>/votes', methods=['POST'])
def vote_on_issue(id):
    try:
        request = flask.request.get_json()
        issue = Issue().vote_from_request_on_issue(request, id)
        return data_response(issue.importance), 200
    except PublicException as e:
        if error_codes.ISSUE_NOT_FOUND == e.error.code:
            e.error.reference.place = 'PATH'
        else:
            e.error.reference.place = 'BODY'
        return error_response(e.error), e.response_code


@app.route('/issues/<int:id>/versions/<int:version>/approved', methods=['PUT'])
def update_issue_version_approval_state(id, version):
    try:
        request = flask.request.get_json()
        issue_version = (
            IssueVersion()
            .change_approval_state_from_request_for_issue_version(
                request, id, version))
        return data_response(issue_version.approved), 200
    except PublicException as e:
        if error_codes.ISSUE_VERSION_NOT_FOUND == e.error.code:
            e.error.reference.place = 'PATH'
        else:
            e.error.reference.place = 'BODY'
        return error_response(e.error), e.response_code


@app.route('/tags', methods=['GET'])
def list_tags():
    tags, pagination = Tag().query_paged_by_args(flask.request.args)
    formatted_tags = [TagFormatter(t).dict for t in tags]
    return data_response(formatted_tags, pagination)


@app.route('/states', methods=['GET'])
def list_states():
    states = State().fetch_all()
    formatted_states = [StateFormatter(s).dict for s in states]
    return data_response(formatted_states)
