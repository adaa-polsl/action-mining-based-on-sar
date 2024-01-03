import pandas as pd

from ..representation.action import Action
from ..representation.action_rule import ActionRule
from ..representation.compound_condition import CompoundCondition
from ..representation.elementary_condition import ElementaryCondition
from .meta_example import MetaExample


class MetaAnalysisResult:
    prime_meta_example: MetaExample
    contra_meta_example: MetaExample
    sourceExamples: pd.DataFrame

    def __init__(
        self,
        ex,
        prime: MetaExample,
        contre: MetaExample,
        set,
    ):
        self.example = ex
        self.prime_meta_example = prime
        self.contra_meta_example = contre
        self.source_examples = set

    def get_action_rule(self):
        rule = ActionRule()
        rule.premise = CompoundCondition()

        premise_left: dict[
            str, ElementaryCondition
        ] = self.prime_meta_example.to_premise()
        premise_right: dict[
            str, ElementaryCondition
        ] = self.contra_meta_example.to_premise()

        intersection_keys = premise_left.keys() & premise_right.keys()
        for key in intersection_keys:
            action = Action(key, premise_left[key], premise_right[key])
            rule.premise.add_subcondition(action)

        return rule
