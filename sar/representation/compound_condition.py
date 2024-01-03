import pandas as pd

from .condition_base import ConditionBase


class CompoundCondition(ConditionBase):
    def __init__(self, subconditions: list[ConditionBase] = None):
        if subconditions:
            self.subconditions: list[ConditionBase] = subconditions
        else:
            self.subconditions = []

    def __repr__(self):
        return (
            "("
            + " AND ".join([str(subcondition) for subcondition in self.subconditions])
            + ")"
        )

    def __str__(self):
        return (
            "("
            + " AND ".join([str(subcondition) for subcondition in self.subconditions])
            + ")"
        )

    def add_subcondition(self, subcondition):
        self.subconditions.append(subcondition)

    def internalEvaluate(self, ex: pd.Series):
        for subcondition in self.subconditions:
            if ex not in subcondition.value_set:
                return False
        return True
