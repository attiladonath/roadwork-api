from __future__ import absolute_import

from sqlalchemy.orm.exc import NoResultFound

import config
from roadworkapi import db
from roadworkapi.models.db_models import Issue as DBIssue
from roadworkapi.controls import Control, IssueVersion
from roadworkapi.controls.mixins import Pagination
from roadworkapi.controls.query.issue import QueryCompiler
from roadworkapi.controls.error import Error, ErrorReference, error_codes
from roadworkapi.controls.exceptions import (
    ConstraintException, ValidationException)


class Issue(Control, Pagination):
    def query_paged_by_args(self, args):
        query = QueryCompiler().compile_from_args(args)
        return self._paged_items_from_query_by_args(query, args)

    @property
    def _max_items_per_page(self):
        return config.ROADWORKAPI_MAX_ISSUES_PER_PAGE

    def create_from_request(self, request):
        issue = DBIssue()
        issue_version = (
            IssueVersion().build_from_request_for_issue(request, issue))
        issue.versions.append(issue_version)

        db.session.add(issue)
        db.session.commit()
        return issue

    def vote_from_request_on_issue(self, request, id):
        try:
            issue = DBIssue.query.filter_by(id=id).one()
        except NoResultFound:
            message = 'Issue is not found (id={}).'.format(id)
            error = Error(
                message, error_codes.ISSUE_NOT_FOUND, ErrorReference('id'))
            raise ValidationException(message, 404, error)

        issue.importance += self._vote_score_from_request(request)

        db.session.add(issue)
        db.session.commit()
        return issue

    def _vote_score_from_request(self, vote):
        self._check_type_string(vote)

        if 'up' == vote:
            return 1
        elif 'down' == vote:
            return -1
        else:
            message = "Vote must be either 'up' or 'down'."
            error = Error(message, error_codes.WRONG_FORMAT)
            raise ConstraintException(message, 422, error)
