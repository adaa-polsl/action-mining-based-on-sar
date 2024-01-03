import toolz
from pandas.api.types import is_numeric_dtype

from ..representation.any_value_set import AnyValueSet
from ..representation.elementary_condition import ElementaryCondition
from ..representation.interval import Interval
from ..representation.rule import Rule
from ..representation.survival_action_rule_set import SurvivalActionRuleSet
from .intersection_finder import IntersectionFinder
from .meta_value import MetaValue


class ActionRangeDistribution:
    def __init__(self, ruleset: SurvivalActionRuleSet, dataset, y):
        self.actions = ruleset
        self.set = dataset
        self.labels = y

        self.dist: dict[str, list[ElementaryCondition]] = {}
        self.splitted_rules: set[Rule] = set()

    def calculate_action_distribution(self) -> None:
        conditions = []
        for rule in self.actions:
            left = rule.get_left_rule()
            right = rule.get_right_rule()
            self.splitted_rules.add(left)
            self.splitted_rules.add(right)
            conditions += [x for x in left.premise.subconditions]
            conditions += [x for x in right.premise.subconditions]

        grouped: dict[str, list[ElementaryCondition]] = {}
        for condition in conditions:
            attribute = condition.attribute
            if attribute not in grouped:
                grouped[attribute] = []
            grouped[attribute].append(condition)

        for attribute, conditions in grouped.items():
            intervals: list[Interval] = []
            result: list[Interval] = []
            split: list[ElementaryCondition]

            current_attribute = self.set[attribute]

            if not is_numeric_dtype(current_attribute):
                intersections = [
                    x.value_set
                    for x in conditions
                    if not isinstance(x.value_set, AnyValueSet)
                ]
                split = list(toolz.unique(intersections, key=lambda x: x.value))

                if len(intersections) == 0:
                    continue

            else:
                intervals = [
                    x.value_set
                    for x in conditions
                    if not isinstance(x.value_set, AnyValueSet)
                ]

                intervals.sort(key=lambda x: x.left, reverse=False)

                if len(intervals) == 0:
                    continue

                result: list[
                    Interval
                ] = IntersectionFinder().calculate_all_intersections(intervals)

                split = result.copy()

            self.dist[attribute] = split

    def get_meta_values_by_attribute(self) -> list[set[MetaValue]]:
        sets = []

        for attribute, value_set_list in self.dist.items():
            meta_values_set = {
                MetaValue(ElementaryCondition(attribute, value_set))
                for value_set in value_set_list
            }
            sets.append(meta_values_set)

        return sets
