class Reference():
    def __init__(self, path=None, place=None):
        if isinstance(path, list):
            self._path = path[::-1]
        else:
            self._path = [path] if path else []

        self.place = place

    def prepend(self, val):
        # It is easier to just store the list in reverse order and use the
        # append() function. When displaying the path it has to be reversed.
        self._path.append(val)
        return self

    def __str__(self):
        # Join reversed path parts with dots.
        path = '.'.join(self._path[::-1])
        # Fix indexing parts, e.g.: list.[1] --> list[1]
        path = path.replace('.[', '[')
        # Join place and path, like: BODY:property
        return ':'.join(filter(None, [self.place, path]))
