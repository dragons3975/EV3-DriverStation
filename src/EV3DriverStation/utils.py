

def get_or_default(iterable, index, default=None):
    if index is None:
        return default
    try:
        return iterable[index]
    except (IndexError, KeyError):
        return default


def index_or_default(iterable, value, default=None):
    try:
        return iterable.index(value)
    except (IndexError, KeyError, ValueError):
        return default