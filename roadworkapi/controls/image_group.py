from __future__ import absolute_import

from roadworkapi import db

from roadworkapi.models.db_models import ImageGroup as DBImageGroup
from roadworkapi.controls import Control, Image
from roadworkapi.controls.exceptions import PublicException


class ImageGroup(Control):
    def build_groups_from_request(self, images):
        self._check_type_list_of_strings(images)
        id = db.session.execute(db.Sequence('image_group_id_seq'))
        image_groups = []
        for i, image_data in enumerate(images):
            image = self._try_process_image_at_index(image_data, i)
            image_groups.append(DBImageGroup(image, group_id=id, weight=i))
        return image_groups

    def _try_process_image_at_index(self, image_data, index):
        try:
            return Image().fetch_or_store_image_from_request(image_data)
        except PublicException as e:
            e.error.reference.prepend('[{}]'.format(index))
            raise
