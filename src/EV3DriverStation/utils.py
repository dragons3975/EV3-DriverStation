import time


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


class AverageOverTime:
    def __init__(self, t):
        self.t = t
        self.data_values = []
        self.data_t = []

    def put(self, value):
        self.clean_old_values()
        self.data_values.append(value)
        self.data_t.append(time.time())

    def clean_old_values(self):
        while len(self.data_t) and time.time() - self.data_t[0] > self.t:
            self.data_t.pop(0)
            self.data_values.pop(0)

    def clear(self):
        self.data_values.clear()
        self.data_t.clear()

    def get(self, default=-1):
        if len(self.data_values) == 0:
            return default
        return sum(self.data_values) / len(self.data_values)
