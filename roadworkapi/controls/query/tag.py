from __future__ import absolute_import

from roadworkapi.models.db_models import Tag


class QueryCompiler():
    STARTS_WITH_ARG = 'starts_with'
    CONTAINS_ARG = 'contains'

    def compile_from_args(self, args):
        query = Tag.query

        starts_with = args.get(self.STARTS_WITH_ARG, None)
        if starts_with:
            query = query.filter(Tag.name.ilike('{}%'.format(starts_with)))

        contains = args.get(self.CONTAINS_ARG, None)
        if contains:
            query = query.filter(Tag.name.ilike('%{}%'.format(contains)))

        return query
