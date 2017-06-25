from __future__ import absolute_import

from geoalchemy2.shape import to_shape

from roadworkapi.controls.image_storage import Factory


class Formatter:
    def __init__(self, model):
        self.model = model

    @property
    def dict(self):
        if self.model is None:
            return {}
        else:
            return self.model_to_dict()


class TagFormatter(Formatter):
    def model_to_dict(self):
        return {
            'name': self.model.name,
            'label': self.model.label
        }


class TagGroupFormatter(Formatter):
    def model_to_dict(self):
        return {
            'tag': TagFormatter(self.model.tag).dict,
            'weight': self.model.weight
        }


class DescriptionFormatter(Formatter):
    def model_to_dict(self):
        return {
            'description': self.model.description
        }


class CoordinatesFormatter(Formatter):
    def model_to_dict(self):
        shape = to_shape(self.model.coordinates)
        return {
            'longitude': shape.x,
            'latitude': shape.y
        }


class StreetviewFormatter(Formatter):
    def model_to_dict(self):
        return {
            'url': self.model.url
        }


class ImageFormatter(Formatter):
    def model_to_dict(self):
        return {
            'url': Factory().storage().url_for_key(self.model.data_key)
        }


class ImageGroupFormatter(Formatter):
    def model_to_dict(self):
        return {
            'image': ImageFormatter(self.model.image).dict,
            'weight': self.model.weight
        }


class StateFormatter(Formatter):
    def model_to_dict(self):
        return {
            'label': self.model.label,
            'name': self.model.name,
            'description': self.model.description,
            'weight': self.model.weight
        }


class IssueFormatter(Formatter):
    def model_to_dict(self):
        versions = sorted(self.model.versions, key=lambda iv: iv.version)

        return {
            'id': self.model.id,
            'importance': self.model.importance,
            'versions': [IssueVersionFormatter(iv).dict for iv in versions]
        }


class IssueVersionFormatter(Formatter):
    def model_to_dict(self):
        m = self.model

        dict = {
            'state': m.state.label,
            'coordinates': CoordinatesFormatter(m.coordinates).dict
        }

        if m.version is not None:
            dict['version'] = int(m.version.strftime('%s'))

        if m.comment is not None:
            dict['comment'] = m.comment

        if 'description' in m.__dict__ or m.description_id:
            if m.description is not None:
                dict['description'] = m.description.description

        if 'tags' in m.__dict__:
            if m.tags:
                dict['tags'] = [t.name for t in m.tags]
        elif 'tag_groups' in m.__dict__ or m.tag_group_id:
            if m.tag_groups:
                tag_groups = sorted(m.tag_groups, key=lambda t: t.weight)
                dict['tags'] = [tg.tag.name for tg in tag_groups]

        if 'images' in m.__dict__:
            if m.images:
                dict['images'] = [i.url for i in m.images]
        elif 'image_groups' in m.__dict__ or m.image_group_id:
            if m.image_groups:
                image_groups = sorted(m.image_groups, key=lambda ig: ig.weight)
                dict['images'] = [
                    ImageFormatter(ig.image).dict['url'] for ig in image_groups
                ]

        if 'streetview' in m.__dict__ or m.streetview_id:
            if m.streetview is not None:
                dict['streetview'] = m.streetview.url

        return dict
