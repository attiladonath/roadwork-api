from __future__ import absolute_import


class Pagination:
    """Mixin, must be mixed into a Control class."""

    def _paged_items_from_query_by_args(self, query, args):
        page_num, items_per_page = self._fetch_paging_arguments(args)
        page = query.paginate(page_num, items_per_page)

        items = page.items
        pagination_data = {
            'total': page.total,
            'pages': page.pages,
            'has_next': page.has_next,
            'has_previous': page.has_prev,
            'next_page': page.next_num,
            'previous_page': page.prev_num
        }

        return items, pagination_data

    def _fetch_paging_arguments(self, args):
        page = self._check_type_int(args.get('page', 1), 'page')
        items_per_page = self._check_type_int(
            args.get('items_per_page', self._max_items_per_page),
            'items_per_page')

        return page, min(items_per_page, self._max_items_per_page)

    @property
    def _max_items_per_page(self):
        raise NotImplementedError()
