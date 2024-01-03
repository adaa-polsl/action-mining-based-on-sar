from .action_rule import ActionRule
from .compound_condition import CompoundCondition
from .elementary_condition import ElementaryCondition
from .survival_rule import SurvivalRule


class SurvivalActionRule(ActionRule):
    def __init__(self, premise: CompoundCondition):
        self.premise: CompoundCondition = premise

    def get_right_rule(self) -> SurvivalRule:
        premise = CompoundCondition(list())
        for subcondition in self.premise.subconditions:
            premise.add_subcondition(
                ElementaryCondition(subcondition.attribute, subcondition.right_value)
            )
        return SurvivalRule(premise)

    def get_left_rule(self) -> SurvivalRule:
        premise = CompoundCondition(list())
        for subcondition in self.premise.subconditions:
            premise.add_subcondition(
                ElementaryCondition(subcondition.attribute, subcondition.left_value)
            )
        return SurvivalRule(premise)
