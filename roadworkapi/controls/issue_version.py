from __future__ import absolute_import

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.session import make_transient
from datetime import datetime

from roadworkapi import db
from roadworkapi.models.db_models import IssueVersion as DBIssueVersion
from roadworkapi.controls import (
    Control, State, Coordinates, Description, TagGroup, ImageGroup, Streetview)
from roadworkapi.controls.error import Error, ErrorReference, error_codes
from roadworkapi.controls.exceptions import (
    PublicException, ValidationException)


class IssueVersion(Control):
    def fetch_all_for_issue_by_id(self, issue_id):
        self._issue_id = self._check_type_int(issue_id)
        return (
            DBIssueVersion.query
            .filter_by(issue_id=issue_id, approved=True)
            .all())

    def build_from_request_for_issue(self, request, issue):
        self._request = self._check_type_dict(request)

        self._issue_version = DBIssueVersion(
            issue,
            self._state_from_request(required=True),
            self._coordinates_from_request(required=True))

        self._fill_issue_version_from_request(skip_required=True)
        return self._issue_version

    def change_approval_state_from_request_for_issue_version(
        self, request, issue_id, version
    ):
        approved = self._check_type_boolean(request)

        try:
            issue_version = (
                DBIssueVersion.query
                .filter_by(issue_id=issue_id)
                .filter(self._version_filter(version))
                .one())
        except NoResultFound:
            message = (
                'IssueVersion is not found (issue_id={}, version={}).'
                .format(issue_id, version))
            error = Error(
                message, error_codes.ISSUE_VERSION_NOT_FOUND,
                ErrorReference('version'))
            raise ValidationException(message, 404, error)

        issue_version.approved = approved
        db.session.add(issue_version)
        db.session.commit()
        return issue_version

    def create_from_request_for_issue_by_id(self, request, issue_id):
        self._request = self._check_type_dict(request)
        self._issue_id = self._check_type_int(issue_id)

        if 'version_to_restore' in self._request:
            version = self._attr_from_request('version_to_restore')
            self._check_type_int(version, 'version_to_restore')
            self._restore_version(version)
        else:
            self._create_version_from_last_approved_version()

        db.session.add(self._issue_version)
        db.session.commit()
        return self._issue_version

    def _restore_version(self, version):
        try:
            self._issue_version = (
                DBIssueVersion.query
                .filter_by(issue_id=self._issue_id,
                           approved=True)
                .filter(self._version_filter(version))
                .one())

            self._detach_issue_version_from_session()
        except NoResultFound:
            message = (
                'IssueVersion is not found (issue_id={}, version={}).'
                .format(self._issue_id, version))
            error = Error(
                message, error_codes.ISSUE_VERSION_NOT_FOUND,
                ErrorReference('version_to_restore'))
            raise ValidationException(message, 404, error)

    def _version_filter(self, version):
        time_low = datetime.fromtimestamp(version)
        time_high = datetime.fromtimestamp(version+1)
        return DBIssueVersion.version.between(time_low, time_high)

    def _create_version_from_last_approved_version(self):
        self._issue_version = self._last_approved_version_of_issue()
        self._detach_issue_version_from_session()
        self._issue_version.comment = self._comment_from_request()
        self._fill_issue_version_from_request()

    def _detach_issue_version_from_session(self):
        make_transient(self._issue_version)
        self._issue_version.version = None

    def _last_approved_version_of_issue(self):
        try:
            return (
                DBIssueVersion.query
                .filter_by(issue_id=self._issue_id, approved=True)
                .order_by(DBIssueVersion.version.desc())
                .one())
        except NoResultFound:
            message = (
                'Latest issue version is not found '
                '(issue_id={}).'.format(self._issue_id))
            error = Error(
                message, error_codes.LATEST_ISSUE_VERSION_NOT_FOUND,
                ErrorReference('id'))
            raise ValidationException(message, 422, error)

    def _fill_issue_version_from_request(self, skip_required=False):
        if not skip_required:
            self._issue_version.state = self._state_from_request()
            self._issue_version.coordinates = self._coordinates_from_request()

        optional_attributes = [
            'comment', 'description', 'tag_groups', 'image_groups',
            'streetview']
        for attr in optional_attributes:
            value = getattr(self, '_{}_from_request'.format(attr))()
            if value:
                setattr(self._issue_version, attr, value)
                if attr in ['tag_groups', 'image_groups']:
                    group_attr = '{}_id'.format(attr[:-1])
                    setattr(self._issue_version, group_attr, value[0].group_id)

    def _state_from_request(self, required=False):
        label = self._attr_from_request('state', required)
        if label is None:
            return None

        try:
            return State().fetch_state_by_label(label)
        except PublicException as e:
            e.error.reference.prepend('state')
            raise

    def _coordinates_from_request(self, required=False):
        coordinates = self._attr_from_request('coordinates', required)
        if coordinates is None:
            return None

        try:
            return Coordinates().build_from_request(coordinates)
        except PublicException as e:
            e.error.reference.prepend('coordinates')
            raise

    def _comment_from_request(self):
        comment = self._attr_from_request('comment')
        if comment is None:
            return None

        return self._check_type_string(comment, 'comment')

    def _description_from_request(self):
        description = self._attr_from_request('description')
        if description is None:
            return None

        try:
            return Description().build_from_request(description)
        except PublicException as e:
            e.error.reference.prepend('description')
            raise

    def _tag_groups_from_request(self):
        tags = self._attr_from_request('tags')
        if tags is None:
            return None

        try:
            return TagGroup().build_groups_from_request(tags)
        except PublicException as e:
            e.error.reference.prepend('tags')
            raise

    def _image_groups_from_request(self):
        images = self._attr_from_request('images')
        if images is None:
            return None

        try:
            return ImageGroup().build_groups_from_request(images)
        except PublicException as e:
            e.error.reference.prepend('images')
            raise

    def _streetview_from_request(self):
        streetview = self._attr_from_request('streetview')
        if streetview is None:
            return None

        try:
            return Streetview().build_from_request(streetview)
        except PublicException as e:
            e.error.reference.prepend('streetview')
            raise
