from .elementary_condition import ElementaryCondition
from .value_set_interface import ValueSetInterface


class Action(ElementaryCondition):
    def __init__(
        self,
        attribute: str,
        left_value: ValueSetInterface,
        right_value: ValueSetInterface,
    ):
        self.attribute: str = attribute
        self.left_value: ValueSetInterface = left_value
        self.right_value: ValueSetInterface = right_value

    def __repr__(self):
        return f"Action({self.attribute}, {self.left_value} -> {self.right_value})"

    def __str__(self):
        return f"({self.attribute}, {self.left_value} -> {self.right_value})"
