from __future__ import absolute_import

from sqlalchemy.exc import DatabaseError, IntegrityError

import config
from roadworkapi import db
from roadworkapi.models.db_models import Tag as DBTag
from roadworkapi.controls import Control
from roadworkapi.controls.error import Error, ErrorReference, error_codes
from roadworkapi.controls.exceptions import ValidationException
from roadworkapi.controls.mixins import Pagination
from roadworkapi.controls.query.tag import QueryCompiler


class Tag(Control, Pagination):
    def query_paged_by_args(self, args):
        query = QueryCompiler().compile_from_args(args)
        return self._paged_items_from_query_by_args(query, args)

    @property
    def _max_items_per_page(self):
        return config.ROADWORKAPI_MAX_TAGS_PER_PAGE

    def fetch_or_create_tags(self, tag_names):
        tags_unsorted = {}
        tags_to_create = list(tag_names)

        # Query existing tags.
        existing_tags = DBTag.query.filter(DBTag.name.in_(tag_names)).all()
        for existing_tag in existing_tags:
            tags_unsorted[existing_tag.name] = existing_tag
            tags_to_create.remove(existing_tag.name)

        # Some new tags need to be created.
        if tags_to_create:
            for tag_name in tags_to_create:
                index = tag_names.index(tag_name)
                tags_unsorted[tag_name] = (
                    self._create_or_fetch_tag(tag_name, index))

        # Sort tags.
        tags = []
        for tag_name in tag_names:
            tags.append(tags_unsorted[tag_name])

        return tags

    def _create_or_fetch_tag(self, tag_name, index):
        try:
            db.session.begin(nested=True)
            return self._try_create_tag(tag_name)
        except IntegrityError:
            try:
                db.session.rollback()
                return self._try_fetch_tag_by_name(tag_name)
            except DatabaseError:
                self._raise_error_with_tag_name_at_index(tag_name, index)
        except DatabaseError:
            self._raise_error_with_tag_name_at_index(tag_name, index)

    def _try_create_tag(self, tag_name):
        tag = DBTag(tag_name)
        db.session.add(tag)
        db.session.commit()
        return tag

    def _try_fetch_tag_by_name(self, tag_name):
        return DBTag.query.filter_by(name=tag_name).one()

    def _raise_error_with_tag_name_at_index(self, tag_name, index):
        message = (
            'Unexpected error while creating tag (name={}).'
            .format(tag_name))
        error = Error(
            message, error_codes.UNEXPECTED_ERROR,
            ErrorReference('[{}]'.format(index)))
        raise ValidationException(message, 422, error)
