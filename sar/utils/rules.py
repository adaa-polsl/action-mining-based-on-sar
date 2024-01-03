import re

from sar.representation import (
    Action,
    AnyValueSet,
    CompoundCondition,
    Interval,
    SingletonSet,
    SurvivalActionRule,
    ValueSetInterface,
)


def str_parse_value_set(value_set_str: str) -> ValueSetInterface:
    try:
        return str_parse_any_value_set(value_set_str)
    except:
        try:
            return str_parse_singleton_set(value_set_str)
        except:
            try:
                return str_parse_interval(value_set_str)
            except:
                raise ValueError(
                    f"Got an incorrect string representation of a ValueSetInterface: {value_set_str!r}"
                )


def str_parse_any_value_set(any_value_set_str: str) -> SingletonSet:
    if any_value_set_str.strip() == "ANY":
        return AnyValueSet()
    else:
        raise ValueError(
            f"Got an incorrect string representation of an any value set: {any_value_set_str!r}"
        )


def str_parse_singleton_set(singleton_set_str: str) -> SingletonSet:
    singleton_set_regex = r"(?<={)(.*?)(?=})"
    match = re.search(singleton_set_regex, singleton_set_str)
    if not match:
        raise ValueError(
            f"Got an incorrect string representation of a singleton set: {singleton_set_str!r}"
        )
    value = match.groups()[0]
    return SingletonSet(value)


def str_parse_interval(interval_str: str) -> Interval:
    number_regex = r"(?:inf|-inf|-?[0-9]+(?:.[0-9]+)?)"
    interval_regex = (
        r"^\s*"
        r"(\<|\()"  # opening bracket
        r"\s*"
        r"(" + number_regex + ")"  # begining of the interval
        r"\s*,\s*"
        r"(" + number_regex + ")"  # end of the interval
        r"\s*"
        r"(\>|\))"  # closing bracket
        r"\s*$"
    )
    match = re.search(interval_regex, interval_str)
    if not match:
        raise ValueError(
            f"Got an incorrect string representation of an interval: {interval_str!r}"
        )
    opening_bracket, left, right, closing_bracket = match.groups()
    left, right = float(left), float(right)
    if left >= right:
        raise ValueError("Interval's left should be smaller than it's right")
    left_closed = opening_bracket == "<"
    right_closed = closing_bracket == ">"

    return Interval(left, right, left_closed, right_closed)


def str_parse_action(action_str: str) -> Action:
    action_regex = r"\(([^,]*),\s*(.*)\s*->\s*(.*)\)"

    match = re.search(action_regex, action_str)
    if not match:
        raise ValueError(
            f"Got an incorrect string representation of an interval: {action_str!r}"
        )
    attribute, left_value_set, right_value_set = match.groups()

    return Action(
        attribute.rstrip(),
        str_parse_value_set(left_value_set.strip()),
        str_parse_value_set(right_value_set.strip()),
    )


def str_parse_compound_condition(compound_condition_str):
    compound_condition_str_list = compound_condition_str.split("AND")
    subconditions = [
        str_parse_action(condition) for condition in compound_condition_str_list
    ]
    return CompoundCondition(subconditions)


def str_parse_sar(sar_str: str) -> SurvivalActionRule:
    conclusion_end = re.search(r"\) THEN \(", sar_str)
    conclusion_start = re.search(r"IF \(", sar_str)
    compound_condition = sar_str[
        conclusion_start.end() - 1 : conclusion_end.start() + 1
    ]

    premise = str_parse_compound_condition(compound_condition)
    return SurvivalActionRule(premise)


def _parse_rule_line(rule_line: str) -> SurvivalActionRule:
    rule_index = re.search(r": IF \(", rule_line)
    sar_str = rule_line[rule_index.start() + 2 :]
    return str_parse_sar(sar_str)


def _parse_rules(rules_lines) -> list[SurvivalActionRule]:
    return [_parse_rule_line(rule_line) for rule_line in rules_lines]


def read_rules(rule_path) -> list[SurvivalActionRule]:
    with open(rule_path, "r") as f:
        contents = f.read()
    lines = contents.split("\n")
    rules_index = lines.index("Rules:")
    rules_lines = lines[rules_index + 1 :]
    rules_lines = list(filter(None, rules_lines))
    rules_list = _parse_rules(rules_lines)
    return rules_list
