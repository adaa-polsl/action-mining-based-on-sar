import pandas as pd

from ..actions.distribution_entry import DistributionEntry
from ..representation.elementary_condition import ElementaryCondition


class MetaValue:
    def __init__(
        self, v: ElementaryCondition = None, d: DistributionEntry = None, rhs=None
    ):
        if rhs is not None:
            self.value = ElementaryCondition(rhs.value.attribute, rhs.value.valueset)
            self.distribution = DistributionEntry(rhs.distribution)
        else:
            self.value = v
            self.distribution = d

    def get_attribute(self):
        return self.value.attribute

    def __contains__(self, example: pd.core.series.Series) -> bool:
        common_attribute: bool = (
            self.get_attribute() if self.get_attribute() in example.index else None
        )
        if common_attribute is None:
            return False
        attribute_value = example[common_attribute]
        return attribute_value in self.value.value_set

    def get_supporting_rules(self):
        return self.distribution.get_all_rules()

    def __str__(self):
        return f"({self.value}, {self.distribution})"

    def __eq__(self, other):
        if not isinstance(other, MetaValue):
            return NotImplemented
        return (self.value, self.distribution) == (other.value, other.distribution)

    def __hash__(self):
        return hash(self.value)
