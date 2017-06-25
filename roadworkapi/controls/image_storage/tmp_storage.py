from __future__ import absolute_import

from tempfile import NamedTemporaryFile

from roadworkapi.controls.image_storage import ImageStorage


class TmpStorage(ImageStorage):
    ROADWORKAPI_IMAGE_URL_FORMAT = 'file://{}'
    ROADWORKAPI_IMAGE_URL_KEY_REGEX = 'file://(.+)'

    def store_image(self, image):
        tmpfile = NamedTemporaryFile(
            suffix=".jpg", prefix="roadworkapi_", delete=False)
        image.save(tmpfile, 'JPEG', quality=90)
        return tmpfile.name

    def url_for_key(self, image_key):
        return self.ROADWORKAPI_IMAGE_URL_FORMAT.format(image_key)
