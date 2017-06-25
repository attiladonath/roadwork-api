from __future__ import absolute_import

from sqlalchemy.sql import func
import geoalchemy2 as ga
import shapely
from unidecode import unidecode

from roadworkapi import db


class BaseModel(db.Model):
    # Tell SQLAlchemy that this is not a mapped class.
    __abstract__ = True

    @property
    def as_dict(self):
        d = {}

        if hasattr(self, 'simple_attributes'):
            for attr in self.simple_attributes:
                val = getattr(self, attr)
                if val:
                    d[attr] = val

        if hasattr(self, 'complex_attributes'):
            for attr in self.complex_attributes:
                # Do not load the attribute (e.g. relationship) if it isn't
                # loaded yet.
                if attr not in self.__dict__:
                    continue

                val = getattr(self, attr)
                # It can be either a singular complex attribute or a list of
                # complex attributes.
                if isinstance(val, list):
                    d[attr] = [element.as_dict for element in val]
                elif val:
                    d[attr] = val.as_dict

        return d


class Tag(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64), unique=True, nullable=False)

    simple_attributes = ['id', 'label', 'name']

    def __init__(self, name):
        self.name = name
        self.label = unidecode(name)


class TagGroup(BaseModel):
    group_id = db.Column(db.Integer, primary_key=True)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'), primary_key=True)
    tag = db.relationship('Tag')
    weight = db.Column(db.SmallInteger, default=0, nullable=False)

    simple_attributes = ['group_id', 'tag_id', 'weight']
    complex_attributes = ['tag']

    def __init__(self, tag, group_id=group_id, weight=None):
        self.tag = tag
        self.group_id = group_id
        self.weight = weight


class Description(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text, nullable=False)

    simple_attributes = ['id', 'description']

    def __init__(self, description):
        self.description = description


class Coordinates(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    coordinates = db.Column(ga.Geometry('POINT', srid=4326), nullable=False)

    simple_attributes = ['id']

    @property
    def as_dict(self):
        d = super(Coordinates, self).as_dict

        if 'coordinates' in self.__dict__:
            shape = ga.shape.to_shape(self.coordinates)
            d['coordinates'] = shapely.wkt.dumps(shape)

        return d

    def __init__(self, longitude, latitude):
        # The database expects the coordinates to be in X-Y order.
        wkt = 'POINT({} {})'.format(longitude, latitude)
        self.coordinates = ga.elements.WKTElement(wkt, srid=4326)


class Streetview(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String, nullable=False)

    simple_attributes = ['id', 'url']

    def __init__(self, url):
        self.url = url


class Image(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    data_key = db.Column(db.String(64), unique=True, nullable=False)

    simple_attributes = ['id', 'data_key']

    def __init__(self, data_key):
        self.data_key = data_key


class ImageGroup(BaseModel):
    group_id = db.Column(db.Integer, primary_key=True)
    image_id = db.Column(
        db.Integer, db.ForeignKey('image.id'), primary_key=True)
    image = db.relationship('Image')
    weight = db.Column(db.SmallInteger, default=0, nullable=False)

    simple_attributes = ['group_id', 'image_id', 'weight']
    complex_attributes = ['image']

    def __init__(self, image, group_id=group_id, weight=None):
        self.image = image
        self.group_id = group_id
        self.weight = weight


class State(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text, nullable=True)
    weight = db.Column(db.SmallInteger, default=0, nullable=False)

    simple_attributes = ['id', 'label', 'name', 'description', 'weight']

    def __init__(self, label, description=None):
        self.label = label
        self.description = description


class Issue(BaseModel):
    id = db.Column(db.Integer, primary_key=True)
    importance = db.Column(db.Integer, default=0, nullable=False)

    versions = db.relationship(
        'IssueVersion',
        primaryjoin='Issue.id==foreign(IssueVersion.issue_id)',
        order_by='IssueVersion.version',
        innerjoin=True
    )

    simple_attributes = ['id', 'importance']
    complex_attributes = ['versions']

    def __init__(self, importance=None):
        self.importance = importance


class IssueVersion(BaseModel):
    issue_id = db.Column(
        db.Integer, db.ForeignKey('issue.id'),
        nullable=False, primary_key=True
    )
    issue = db.relationship('Issue')

    version = db.Column(
        db.DateTime, server_default=func.now(),
        nullable=False, primary_key=True
    )

    approved = db.Column(db.Boolean, nullable=True)

    comment = db.Column(db.Text, nullable=True)

    state_id = db.Column(db.Integer, db.ForeignKey('state.id'), nullable=False)
    state = db.relationship('State', innerjoin=True)

    coordinates_id = db.Column(
        db.Integer, db.ForeignKey('coordinates.id'), nullable=False)
    coordinates = db.relationship('Coordinates', innerjoin=True)

    description_id = db.Column(
        db.Integer, db.ForeignKey('description.id'), nullable=True)
    description = db.relationship('Description')

    tag_group_id = db.Column(db.Integer, nullable=True)
    tag_groups = db.relationship(
        'TagGroup',
        primaryjoin='IssueVersion.tag_group_id==foreign(TagGroup.group_id)',
        order_by='TagGroup.weight'
    )
    tags = db.relationship(
        'Tag',
        secondary='tag_group',
        primaryjoin='IssueVersion.tag_group_id==foreign(TagGroup.group_id)',
        secondaryjoin='Tag.id==foreign(TagGroup.tag_id)',
        order_by='TagGroup.weight'
    )

    image_group_id = db.Column(db.Integer, nullable=True)
    image_groups = db.relationship(
        'ImageGroup',
        primaryjoin=(
            'IssueVersion.image_group_id==foreign(ImageGroup.group_id)'),
        order_by='ImageGroup.weight'
    )
    images = db.relationship(
        'Image',
        secondary='image_group',
        primaryjoin=(
            'IssueVersion.image_group_id==foreign(ImageGroup.group_id)'),
        secondaryjoin='Image.id==foreign(ImageGroup.image_id)',
        order_by='ImageGroup.weight'
    )

    streetview_id = db.Column(
        db.Integer, db.ForeignKey('streetview.id'), nullable=True)
    streetview = db.relationship('Streetview')

    simple_attributes = [
        'issue_id', 'version', 'comment', 'state_id', 'coordinates_id',
        'description_id', 'tag_group_id', 'image_group_id',
        'streetview_id']
    complex_attributes = [
        'issue', 'state', 'coordinates', 'description', 'tag_groups', 'tags',
        'image_groups', 'images', 'streetview']

    def __init__(self, issue, state, coordinates):
        self.issue = issue
        self.state = state
        self.coordinates = coordinates
