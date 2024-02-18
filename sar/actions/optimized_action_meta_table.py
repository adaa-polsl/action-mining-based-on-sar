from copy import copy
from typing import Optional, Tuple
import pandas as pd
import logging

from ..representation.elementary_condition import ElementaryCondition
from ..representation.singleton_set import SingletonSet
from .action_meta_table import ActionMetaTable
from .action_range_distribution import ActionRangeDistribution
from .meta_analysis_result import MetaAnalysisResult
from .meta_example import MetaExample
from .meta_value import MetaValue
from concurrent.futures import ThreadPoolExecutor

log = logging.getLogger(__name__)


class OptimizedActionMetaTable(ActionMetaTable):
    stable_attributes: list[str] = []

    def __init__(
        self,
        distribution: ActionRangeDistribution,
        quality_function,
        stable_attributes,
        target,
        method,
        estimator,
        encoder,
    ):
        super().__init__(
            distribution, quality_function, target, method, estimator, encoder
        )
        self.stable_attributes: list[str] = stable_attributes
        self.meta_values_by_attribute: dict[str, list[MetaValue]] = {}
        for meta_values in self.meta_values_list:
            to_add = set(meta_values)
            attribute = next(iter(meta_values)).value.attribute
            self.meta_values_by_attribute[attribute] = to_add
        self.meta_values_by_attribute_local = {
            k: set(v) for k, v in self.meta_values_by_attribute.items()
        }

    def analyze(
        self,
        ex,
        pruning_enabled: bool,
        generate_multiple_recommendations: bool,
    ) -> list[MetaAnalysisResult]:
        ret: list[MetaAnalysisResult] = []
        prime_me: MetaExample = MetaExample()
        allowed_attributes: set[str] = set()

        meta_values_by_attribute_local = {}
        for attribute, meta_values in self.meta_values_by_attribute.items():
            meta_values_by_attribute_local[attribute] = set(meta_values)

        proposed_prime: list[MetaValue] = []

        for meta_values in meta_values_by_attribute_local.values():
            for meta_value in meta_values:
                if ex in meta_value:
                    proposed_prime.append(meta_value)
                    break

        for prime in proposed_prime:
            prime_me.add(prime)

        if not prime_me.get_all_values():
            raise Exception(f"The example {ex} was not covered by any metaexample")

        for key in list(meta_values_by_attribute_local.keys()):
            meta_values_by_attribute_local[key] = {
                z for z in meta_values_by_attribute_local[key] if ex not in z
            }

        while True:
            attributes: list[str] = list(self.train_set.columns)
            for attribute in attributes:
                if attribute in self.stable_attributes:
                    continue
                allowed_attributes.add(attribute)

            contra_me = MetaExample()
            best_q: float = self.rank_meta_premise(contra_me, ex, self.train_set)
            grown = True
            pruned: bool = pruning_enabled

            while grown:
                best: MetaValue = self.get_best_meta_value(
                    ex,
                    allowed_attributes,
                    contra_me,
                    self.train_set,
                )

                if best == None:
                    break

                contra_me.add(best)
                curr_q: float = self.rank_meta_premise(contra_me, ex, self.train_set)

                if curr_q >= best_q:
                    allowed_attributes.remove(best.get_attribute())

                    best_q = curr_q
                    grown = True
                    log.debug(f"Found best meta-value: {best} at quality {best_q}")
                else:
                    contra_me.remove(best)
                    grown = False

                if curr_q == 1.0:
                    grown = False

            while pruned:
                candidate_to_removal = None
                curr_q = 0.0
                current_values = copy(contra_me)

                for mv in current_values.get_all_values():
                    contra_me.remove(mv)

                    q = self.rank_meta_premise(contra_me, ex, self.train_set)

                    if q >= curr_q:
                        curr_q = q
                        candidate_to_removal = mv

                    contra_me.add(mv)

                if candidate_to_removal is not None and curr_q >= best_q:
                    contra_me.remove(candidate_to_removal)
                    best_q = curr_q
                else:
                    pruned = False

            if contra_me.get_size() == 0:
                break
            else:
                meta_value: MetaValue
                for meta_value in contra_me.get_all_values():
                    if (
                        meta_value
                        in meta_values_by_attribute_local[meta_value.get_attribute()]
                    ):
                        meta_values_by_attribute_local[
                            meta_value.get_attribute()
                        ].remove(meta_value)

            result: MetaAnalysisResult = MetaAnalysisResult(
                ex, prime_me, contra_me, self.train_set
            )
            ret.append(result)

            if not generate_multiple_recommendations:
                break

        return ret

    def generate_extended_allowed_list(self, allowed):
        extended_allowed_dict = {}
        for attribute, meta_values in allowed.items():
            if isinstance(list(meta_values)[0].value.value_set, SingletonSet):
                extended_allowed_dict[attribute] = meta_values
                continue
            meta_values_sorted = sorted(
                meta_values, key=lambda x: x.value.value_set.left
            )
            extended_meta_values_set = set()
            for i, meta_value in enumerate(meta_values_sorted):
                for meta_value_2 in meta_values_sorted[i:]:
                    new_value_set = meta_value.value.value_set.get_union(
                        meta_value_2.value.value_set
                    )
                    new_meta_value = MetaValue(
                        ElementaryCondition(attribute, new_value_set)
                    )
                    extended_meta_values_set.add(new_meta_value)
            extended_allowed_dict[attribute] = extended_meta_values_set
        return extended_allowed_dict

    def get_best_meta_value(
        self,
        example: pd.Series,
        allowed_attributes: set[str],
        contra: MetaExample,
        examples,
    ) -> Optional[MetaValue]:
        best_quality = float("-inf")

        allowed: dict[str, set[MetaValue]] = {
            k: v
            for k, v in self.meta_values_by_attribute_local.items()
            if k in allowed_attributes
        }
        attributes: list[str] = list(allowed_attributes)
        atr_to_int: dict[str, int] = {attr: idx for idx, attr in enumerate(attributes)}
        candidates: list[Optional[MetaValue]] = [None] * len(attributes)
        qualities: list[float] = [best_quality] * len(attributes)

        def process_item(x: Tuple[str, set[MetaValue]]):
            local_contra = copy(contra)
            index = atr_to_int[x[0]]
            quality = qualities[index]

            for cand in x[1]:
                local_contra.add(cand)
                q = self.rank_meta_premise(local_contra, example, examples)
                local_contra.remove(cand)

                if q >= quality:
                    candidates[index] = cand
                    qualities[index] = q
                    quality = q

        with ThreadPoolExecutor() as executor:
            executor.map(process_item, list(allowed.items()))

        if not qualities:
            return None

        max_quality = max(qualities)
        idx = qualities.index(max_quality)
        return candidates[idx]
