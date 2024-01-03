from .value_set_interface import ValueSetInterface


class SingletonSet(ValueSetInterface):
    def __init__(self, value: str) -> None:
        """Initialize an SingletonSet object from a string representation of a set
        e.g: SingletonSet('{N}')"""
        self.value = value

    def __contains__(self, value: float) -> bool:
        return self.value == value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SingletonSet):
            return self.value == other.value
        else:
            return False

    def __repr__(self) -> str:
        return f"SingletonSet({self.__str__()!r})"

    def __str__(self) -> str:
        return "{" + self.value + "}"
