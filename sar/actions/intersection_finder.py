from ..representation.interval import Interval


class IntersectionFinder:
    def __init__(self):
        pass

    def calculate_all_intersections(self, intervals: list[Interval]) -> list[Interval]:
        points = []
        points.append(float("-inf"))
        points.append(float("inf"))
        for i in range(len(intervals) - 1):
            offset = 1
            current_interval = intervals[i]
            next_interval = intervals[i + offset]

            points.append(current_interval.left)
            points.append(current_interval.right)

            while current_interval.intersects(next_interval):
                intersection = current_interval.get_intersection(next_interval)
                points.append(intersection.left)
                points.append(intersection.right)

                offset += 1
                if i + offset >= len(intervals):
                    break
                next_interval = intervals[i + offset]

        points.append(intervals[-1].left)
        points.append(intervals[-1].right)

        pts = list(set(points))
        pts.sort()
        result: list[Interval] = []

        if pts[0] == float("-inf"):
            result.append(Interval(float("-inf"), pts[1], False, True))
        else:
            result.append(Interval(float("-inf"), pts[0], False, True))

        for i in range(1, len(pts) - 2):
            result.append(Interval(pts[i], pts[i + 1], False, True))

        if pts[-1] == float("inf"):
            result.append(Interval(pts[-2], float("inf"), False, False))
        else:
            result.append(Interval(pts[-1], float("inf"), False, False))

        return result
