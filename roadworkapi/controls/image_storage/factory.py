from __future__ import absolute_import

import config
from roadworkapi.controls.exceptions import RoadworkApiException


class Factory:
    def storage(self):
        if 'tmp' == config.ROADWORKAPI_IMAGE_STORAGE:
            from roadworkapi.controls.image_storage import TmpStorage
            return TmpStorage()
        else:
            raise RoadworkApiException(
                'Unknown image storage "{}"'
                .format(config.ROADWORKAPI_IMAGE_STORAGE))
