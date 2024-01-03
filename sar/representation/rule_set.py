from sar.representation.rule import Rule

from .survival_action_rule import SurvivalActionRule


class RuleSet:
    def __init__(self, rules: list[SurvivalActionRule] = []):
        self.rules = rules

    def add_rule(self, rule: Rule):
        self.rules.append(rule)
