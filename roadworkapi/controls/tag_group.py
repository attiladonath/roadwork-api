from __future__ import absolute_import

from roadworkapi import db

from roadworkapi.models.db_models import TagGroup as DBTagGroup
from roadworkapi.controls import Control, Tag


class TagGroup(Control):
    def build_groups_from_request(self, tag_names):
        self._check_type_list_of_strings(tag_names)
        tags = Tag().fetch_or_create_tags(tag_names)

        id = db.session.execute(db.Sequence('tag_group_id_seq'))
        tag_groups = []
        for i, tag in enumerate(tags):
            tag_groups.append(DBTagGroup(tag, group_id=id, weight=i))
        return tag_groups
