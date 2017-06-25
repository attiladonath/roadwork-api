from __future__ import absolute_import

import re
import base64
from PIL import Image as PILImage
from PIL import ExifTags
from cStringIO import StringIO
from sqlalchemy.orm.exc import NoResultFound

import config
from roadworkapi import db
from roadworkapi.models.db_models import Image as DBImage
from roadworkapi.controls import Control
from roadworkapi.controls.image_storage import Factory
from roadworkapi.controls.error import Error, error_codes
from roadworkapi.controls.exceptions import ValidationException


class Image(Control):
    def fetch_or_store_image_from_request(self, image):
        # Check if the image is an existing one.
        image_key = self._image_key_from_url(image)
        if image_key:
            return self.fetch_image_by_key(image_key)

        # Pretend that the image is a new one encoded in base64.
        try:
            image_data = base64.b64decode(image)
            image_key = self._store_image(image_data)
            image = DBImage(image_key)

            db.session.add(image)
            db.session.commit()
            return image
        except TypeError:
            message = 'Image is not base64 decodable.'
            error = Error(message, error_codes.IMAGE_NOT_BASE64)
            raise ValidationException(message, 422, error)

    def _image_key_from_url(self, url):
        key_regex = Factory().storage().ROADWORKAPI_IMAGE_URL_KEY_REGEX
        match = re.match(key_regex, url)
        if match is None:
            return None
        return match.group(1)

    def fetch_image_by_key(self, key):
        try:
            return DBImage.query.filter_by(data_key=key).one()
        except NoResultFound:
            message = 'Image is not found in the database.'
            error = Error(message, error_codes.IMAGE_NOT_FOUND)
            raise ValidationException(message, 422, error)

    def _store_image(self, image_data):
        try:
            image_stream = StringIO(image_data)
            image = PILImage.open(image_stream)
            image = self._rotate_image_based_on_exif(image)
            maxsize = config.ROADWORKAPI_IMAGE_MAX_DIMENSIONS
            image.thumbnail(maxsize, PILImage.ANTIALIAS)
            return Factory().storage().store_image(image)
        except IOError as e:
            message = 'Image is of an unknown format.'
            error = Error(message, error_codes.IMAGE_UNKNOWN_FORMAT)
            raise ValidationException(message, 422, error)

    def _rotate_image_based_on_exif(self, image):
        try:
            exif = dict(image._getexif().items())

            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation':
                    break

            if not exif[orientation]:
                return image

            if exif[orientation] == 3:
                degree = 180
            elif exif[orientation] == 6:
                degree = 270
            elif exif[orientation] == 8:
                degree = 90
            else:
                return image

            return image.rotate(degree, expand=True)
        except:
            return image
