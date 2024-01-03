from abc import ABC
from copy import deepcopy

import pandas as pd
from sksurv.functions import StepFunction
from sksurv.nonparametric import kaplan_meier_estimator

from ..utils.stats import test_diff
from .action_range_distribution import ActionRangeDistribution
from .meta_analysis_result import MetaAnalysisResult
from .meta_example import MetaExample
from .meta_value import MetaValue


class ActionMetaTable(ABC):
    metaValuesList: list[set[MetaValue]]

    def __init__(
        self,
        distribution: ActionRangeDistribution,
        quality_function,
        target,
        method,
        estimator,
        encoder,
    ):
        self.train_set = deepcopy(distribution.set)
        self.train_labels = deepcopy(distribution.labels)
        self.meta_values_list: list[
            set[MetaValue]
        ] = distribution.get_meta_values_by_attribute()
        self.quality_measure = quality_function
        self.target = target
        self.method = method
        self.estimator = estimator
        self.encoder = encoder

    def analyze(
        self,
        ex,
        pruningEnabled: bool,
        generateMultipleRecommendations: bool,
    ) -> list[MetaAnalysisResult]:
        pass

    def rank_meta_premise(
        self,
        meta_premise: MetaExample,
        current_sample: pd.Series,
        examples,
    ) -> float:
        from ..utils.mutator import Mutator
        from ..utils.processing import encode

        current_sample_surv_func = self.estimator.predict_survival_function(
            pd.DataFrame(encode(current_sample, self.estimator, self.encoder)).T,
            return_array=False,
        )[0]
        if self.method == "est":
            new_sample = Mutator().mutate_sample(current_sample, meta_premise, examples)
            new_sample_surv_func = self.estimator.predict_survival_function(
                pd.DataFrame(encode(new_sample, self.estimator, self.encoder)).T,
                return_array=False,
            )[0]
        elif self.method == "km":
            X_coverage, y_coverage = meta_premise.covers(
                self.train_set, self.train_labels
            )
            if len(X_coverage) < 20:
                return 0.0
            time, survival_prob = kaplan_meier_estimator(
                y_coverage["cens"].astype(bool), y_coverage["time"]
            )
            new_sample_surv_func = StepFunction(time, survival_prob)
        else:
            raise ValueError("'method' must be 'estimator', or 'km'")

        statistic, pvalue = test_diff(current_sample_surv_func, new_sample_surv_func)
        return statistic
