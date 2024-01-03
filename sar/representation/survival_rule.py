from .compound_condition import CompoundCondition
from .elementary_condition import ElementaryCondition
from .rule import Rule


class SurvivalRule(Rule):
    def __init__(
        self, premise: CompoundCondition, consequence: ElementaryCondition = None
    ):
        super().__init__(premise, consequence)
