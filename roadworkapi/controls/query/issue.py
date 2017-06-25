from __future__ import absolute_import

import sqlalchemy as sa
import geoalchemy2 as ga
from shapely.geometry import Point
import copy


from roadworkapi import db
from roadworkapi.models.db_models import (
    Issue, IssueVersion, Coordinates, State, Tag, TagGroup)
from roadworkapi.controls.error import Error, ErrorReference, error_codes
from roadworkapi.controls.exceptions import (
    ConstraintException, ValidationException)


class QueryCompiler():
    ARGUMENTS = ['distance', 'states', 'tags', 'sort']

    def compile_from_args(self, args):
        self._arguments = Arguments(args)
        self._ordered_by_update_date = False
        self._joined_models = []

        self._compile_base_query()
        self._add_argument_based_modifications()

        if not self._ordered_by_update_date:
            self._apply_default_sorting()

        return self._query

    def _compile_base_query(self):
        latest_versions = (
            db.session.query(
                IssueVersion.issue_id,
                sa.func.max(IssueVersion.version).label('version'))
            .filter(IssueVersion.approved)
            .group_by(IssueVersion.issue_id)
            .subquery())

        issue_version_load = sa.orm.contains_eager(Issue.versions)
        issue_version_load.joinedload(IssueVersion.state)
        issue_version_load.joinedload(IssueVersion.coordinates)
        issue_version_load.joinedload(IssueVersion.description)
        issue_version_load.joinedload(IssueVersion.tags)
        issue_version_load.joinedload(IssueVersion.images)
        issue_version_load.joinedload(IssueVersion.streetview)

        self._query = (
            Issue.query
            .options(issue_version_load)
            .join(IssueVersion)
            .join(
                latest_versions,
                sa.and_(
                    IssueVersion.issue_id == latest_versions.c.issue_id,
                    IssueVersion.version == latest_versions.c.version))
        )

    def _add_argument_based_modifications(self):
        for argument in self.ARGUMENTS:
            if getattr(self._arguments, argument) is not None:
                processor = getattr(
                    self, '_add_modification_based_on_{}'.format(argument))
                processor()

    def _add_modification_based_on_distance(self):
        self._add_join_once(Coordinates)
        self._query = (
            self._query
            .filter(ga.functions.ST_Distance_Sphere(
                Coordinates.coordinates,
                self._arguments.around) <= self._arguments.distance))

    def _add_modification_based_on_states(self):
        self._add_join_once(State)
        self._query = (
            self._query
            .filter(State.label.in_(self._arguments.states)))

    def _add_modification_based_on_tags(self):
        tag_group_ids = (
            TagGroup.query.with_entities(TagGroup.group_id)
            .join(Tag)
            .filter(Tag.name.in_(self._arguments.tags))
            .group_by(TagGroup.group_id)
            .having(sa.func.count(
                TagGroup.tag_id) == len(self._arguments.tags)))

        self._query = (
            self._query
            .filter(IssueVersion.tag_group_id.in_(tag_group_ids)))

    def _add_modification_based_on_sort(self):
        for label, direction in self._arguments.sort:
            if 'distance' == label:
                distance = ga.functions.ST_Distance_Sphere(
                    Coordinates.coordinates,
                    self._arguments.around)
                self._add_join_once(Coordinates)
                self._query = (
                    self._query
                    .order_by(getattr(distance, direction)()))

            if 'state' == label:
                self._add_join_once(State)
                self._query = (
                    self._query
                    .order_by(getattr(State.weight, direction)()))

            if 'vote' == label:
                self._query = (
                    self._query
                    .order_by(getattr(Issue.importance, direction)()))

            if 'creation_date' == label:
                self._query = (
                    self._query
                    .order_by(getattr(Issue.id, direction)()))

            if 'update_date' == label:
                self._ordered_by_update_date = True
                self._query = (
                    self._query
                    .order_by(getattr(IssueVersion.version, direction)()))

    def _apply_default_sorting(self):
        # By default order issues by date, latest first.
        self._query = (
            self._query
            .order_by(IssueVersion.version.desc()))

    def _add_join_once(self, model_class):
        if model_class not in self._joined_models:
            self._query = self._query.join(model_class)
            self._joined_models.append(model_class)


class Arguments():
    ARGUMENTS = ['around', 'distance', 'states', 'tags', 'sort']
    SORT_LABELS = ['distance', 'state', 'vote', 'creation_date', 'update_date']

    def __init__(self, request_args):
        self._request_args = request_args
        self._process_arguments()

    def _process_arguments(self):
        self._fetch_and_process_raw_arguments()
        self._check_constraints()

    def _fetch_and_process_raw_arguments(self):
        for argument in self.ARGUMENTS:
            value = self._request_args.get(argument, None)
            if value is not None:
                processed_value = self._call_processor_function(
                    argument, value)
                setattr(self, argument, processed_value)
            else:
                setattr(self, argument, None)

    def _call_processor_function(self, argument, value):
        processor = getattr(self, '_process_argument_{}'.format(argument))
        return processor(value)

    def _process_argument_around(self, value):
        try:
            longitude, latitude = value.split(',')
            point = Point(float(longitude), float(latitude))
            return ga.elements.WKTElement(point.to_wkt(), srid=4326)
        except ValueError:
            message = (
                "The argument 'around' must be in "
                "'{float longitude},{float latitude}' format.")
            error = Error(
                message, error_codes.WRONG_FORMAT, ErrorReference('around'))
            raise ConstraintException(message, 422, error)

    def _process_argument_distance(self, value):
        try:
            # Convert kilometers to meters.
            return float(value) * 1000
        except ValueError:
            message = "The argument 'distance' must be a number."
            error = Error(
                message, error_codes.WRONG_TYPE, ErrorReference('distance'))
            raise ConstraintException(message, 422, error)

    def _process_argument_states(self, value):
        state_labels = value.split(',')
        state_labels_check = copy.copy(state_labels)

        states = State.query.filter(State.label.in_(state_labels)).all()
        for state in states:
            state_labels_check.remove(state.label)

        if len(state_labels_check):
            message = (
                "The argument 'states' contains unknown state(s) "
                "'{}'.".format("', '".join(state_labels)))
            error = Error(
                message, error_codes.STATE_NOT_FOUND, ErrorReference('states'))
            raise ValidationException(message, 422, error)

        return state_labels

    def _process_argument_tags(self, value):
        tag_names = value.split(',')
        tag_names_check = copy.copy(tag_names)

        tags = Tag.query.filter(Tag.name.in_(tag_names)).all()
        for tag in tags:
            tag_names_check.remove(tag.name)

        if len(tag_names_check):
            message = (
                "The argument 'tags' contains unknown tag(s) "
                "'{}'.".format("', '".join(tag_names)))
            error = Error(
                message, error_codes.TAGS_NOT_FOUND, ErrorReference('tags'))
            raise ValidationException(message, 422, error)

        return tag_names

    def _process_argument_sort(self, value):
        sortings = []
        sorting_labels = value.split(',')
        unknown_labels = []

        for sorting_label in sorting_labels:
            label, direction = (
                self._label_and_direction_from_sorting_label(sorting_label))
            if label in self.SORT_LABELS:
                sortings.append((label, direction))
            else:
                unknown_labels.append(label)

        if len(unknown_labels):
            message = (
                "The argument 'sort' contains unknown labels "
                "'{}'.".format("', '".join(unknown_labels)))
            error = Error(
                message, error_codes.UNKNOWN_SORT_LABELS,
                ErrorReference('sort'))
            raise ValidationException(message, 422, error)

        return sortings

    def _label_and_direction_from_sorting_label(self, sorting_label):
        if '-' == sorting_label[0]:
            return sorting_label[1:], 'desc'
        else:
            return sorting_label, 'asc'

    def _check_constraints(self):
        if self.distance is not None and self.around is None:
            message = (
                "The argument 'distance' can only be used if 'around' is "
                "given.")
            error = Error(
                message, error_codes.REQUIRED_ATTRIBUTE_MISSING,
                ErrorReference('around'))
            raise ConstraintException(message, 422, error)

        if self.sort is not None and self.around is None:
            for label, direction in self.sort:
                if 'distance' == label:
                    message = (
                        "Sorting by distance can only be used if 'around' "
                        "argument is given.")
                    error = Error(
                        message, error_codes.REQUIRED_ATTRIBUTE_MISSING,
                        ErrorReference('around'))
                    raise ConstraintException(message, 422, error)
