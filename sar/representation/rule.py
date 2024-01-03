import pandas as pd

from .compound_condition import CompoundCondition
from .elementary_condition import ElementaryCondition


class Rule:
    def __init__(
        self, premise: CompoundCondition, consequence: ElementaryCondition = None
    ):
        self.premise: CompoundCondition = premise
        self.consequence: ElementaryCondition = consequence

    def covers(self, X: pd.DataFrame, y: pd.DataFrame, left=False):
        X = X.copy().reset_index(drop=True)

        def is_row_matching_meta(row):
            if left:
                return all(
                    (
                        action.left_value is None
                        or row[action.attribute] in action.left_value.value_set
                    )
                    for action in self.premise.subconditions
                )
            else:
                return all(
                    (
                        action.right_value is None
                        or row[action.attribute] in action.right_value.value_set
                    )
                    for action in self.premise.subconditions
                )

        is_covered = X.apply(is_row_matching_meta, axis=1)
        X_covered = X[is_covered]
        y_covered = y[X_covered.index]

        return X_covered, y_covered
