from .condition_base import ConditionBase
from .value_set_interface import ValueSetInterface


class ElementaryCondition(ConditionBase):
    def __init__(self, attribute: str, value_set: ValueSetInterface):
        self.attribute: str = attribute
        self.value_set: ValueSetInterface = value_set

    def __str__(self):
        return f"({self.attribute}, {self.value_set})"
