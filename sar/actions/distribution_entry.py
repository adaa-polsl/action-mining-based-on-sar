from ..representation.elementary_condition import ElementaryCondition
from ..representation.rule import Rule
from ..representation.value_set_interface import ValueSetInterface


class DistributionEntry:
    def __init__(self, rhs=None):
        self.distribution: list[ElementaryCondition] = []

    def add(self, class_value: ValueSetInterface, rule: Rule):
        if class_value not in self.distribution:
            self.distribution[class_value] = []
        self.distribution[class_value].append(rule)

    def add(self, rule: Rule):
        self.distribution.append(rule)

    def get_all_rules(self) -> list[Rule]:
        return [rule for rules in self.distribution.values() for rule in rules]

    def get_rules_of_class(self, class_id):
        return self.distribution.get(class_id)

    def __eq__(self, other):
        if isinstance(other, DistributionEntry):
            return self.distribution == other.distribution
        return False

    def __hash__(self):
        return hash(frozenset(self.distribution.items()))
