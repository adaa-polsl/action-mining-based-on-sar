from copy import copy

import pandas as pd

from ..representation.rule import Rule
from .meta_value import MetaValue


class MetaExample:
    data: dict[str, MetaValue]
    rules: set[Rule]

    def __init__(self):
        self.data = {}

    def add(self, meta_value: MetaValue):
        self.data[meta_value.get_attribute()] = meta_value

    def remove(self, meta_value: "MetaValue"):
        attribute = meta_value.get_attribute()
        if attribute in self.data:
            self.data.pop(attribute)

    def get_size(self):
        return len(self.data)

    def get_all_values(self) -> list[MetaValue]:
        return self.data.values()

    def __copy__(self):
        new_instance = MetaExample()
        new_instance.data = copy(self.data)
        if hasattr(self, "rules"):
            new_instance.rules = copy(self.rules)
        return new_instance

    def to_premise(self):
        result = {}
        for key in self.data:
            mv = self.data[key]
            value = mv.value
            result[value.attribute] = value
        return result

    def covers(self, X: pd.DataFrame, y: pd.DataFrame):
        X = X.copy().reset_index(drop=True)

        def is_row_matching_meta(row):
            return all(row in self.data[attribute] for attribute in self.data.keys())

        is_covered = X.apply(is_row_matching_meta, axis=1)
        X_covered = X[is_covered]
        y_covered = y[X_covered.index]

        return X_covered, y_covered
