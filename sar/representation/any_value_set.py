from .value_set_interface import ValueSetInterface


class AnyValueSet(ValueSetInterface):
    def __init__(self) -> None:
        pass

    def __contains__(self, value: float) -> bool:
        return True

    def __eq__(self, other: object) -> bool:
        if isinstance(other, AnyValueSet):
            return True
        else:
            return False

    def __repr__(self) -> str:
        return f"SingletonSet({self.__str__()!r})"

    def __str__(self) -> str:
        return "ANY"
