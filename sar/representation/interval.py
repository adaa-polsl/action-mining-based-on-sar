from .any_value_set import AnyValueSet
from .value_set_interface import ValueSetInterface


class Interval(ValueSetInterface):
    def __init__(
        self,
        left: float,
        right: float,
        left_closed: bool = False,
        right_closed: bool = False,
    ) -> None:
        """Initialize an Interval object from a string representation of an interval
        e.g: Interval('(3,4]')"""

        self.left: float = left
        self.right: float = right
        self.left_closed: bool = left_closed
        self.right_closed: bool = right_closed

    def __eq__(self, other: object):
        if isinstance(other, Interval):
            return (
                (self.left == other.left)
                & (self.right == other.right)
                & (self.left_closed == other.left_closed)
                & (self.right_closed == other.right_closed)
            )
        else:
            return False

    def __repr__(self) -> str:
        return f"Interval({self.__str__()!r})"

    def __str__(self) -> str:
        opening_bracket = "<" if self.left_closed else "("
        closing_bracket = ">" if self.right_closed else ")"
        if self.left == float("-inf") and self.right == float("inf"):
            return "ANY"
        else:
            return f"{opening_bracket}{self.left}, {self.right}{closing_bracket}"

    def __contains__(self, x: float) -> bool:
        if self.left < x < self.right:
            return True
        if x == self.left:
            return self.left_closed
        if x == self.right:
            return self.right_closed

    def intersects(self, set: ValueSetInterface) -> bool:
        if isinstance(set, AnyValueSet):
            return True

        ds = set if isinstance(set, Interval) else None
        if ds is not None:
            if (
                self.right < ds.left
                or (self.right == ds.left and not ds.left_closed)
                or self.left > ds.right
                or (self.left == ds.right and not ds.right_closed)
            ):
                return False
            else:
                return True

        return False

    def get_intersection(self, set):
        if isinstance(set, AnyValueSet):
            return self
        if isinstance(set, Interval):
            other = set
            if not self.intersects(other):
                return None
            return Interval(
                max(self.left, other.left),
                min(self.right, other.right),
                other.left_closed if self.left < other.left else self.left_closed,
                other.right_closed if self.right > other.right else self.right_closed,
            )
        else:
            return None

    def get_union(self, set):
        min_left = min(set.left, self.left)
        max_right = max(set.right, self.right)
        left_closed = any([set.left_closed, self.left_closed])
        right_closed = any([set.right_closed, self.right_closed])
        return Interval(min_left, max_right, left_closed, right_closed)
