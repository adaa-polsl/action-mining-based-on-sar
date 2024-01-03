import os

import numpy as np
import pandas as pd
from scipy.stats import ks_2samp
from sksurv.functions import StepFunction
from sksurv.nonparametric import kaplan_meier_estimator

from sar.utils.processing import encode


def test_diff(sf1: StepFunction, sf2: StepFunction) -> float:
    if len(sf1.x) != len(sf2.x) or np.any(sf1.x != sf2.x):
        domain_min = max(sf1.x.min(), sf2.x.min())
        domain_max = min(sf1.x.max(), sf2.x.max())
        x1 = [x for x in set(sf1.x) if (x > domain_min) & (x < domain_max)]
        x2 = [x for x in set(sf2.x) if (x > domain_min) & (x < domain_max)]
        domain = list(set(x1).union(set(x2)))
    else:
        domain = sf1.x

    y1, y2 = [], []
    for x in domain:
        y1.append(sf1(x))
        y2.append(sf2(x))
    statistic, pvalue = ks_2samp(y1, y2)
    return statistic, pvalue


def calc_diff(
    sample_set,
    recommendations,
    X_train,
    y_train,
    estimator,
    encoder,
    fold_path,
):
    results_dir = os.path.join(fold_path, "diff")
    os.makedirs(results_dir, exist_ok=True)
    results = pd.DataFrame()
    for idx, (_, sample) in enumerate(sample_set.iterrows()):
        action_rule = recommendations.rules[idx]

        sample_surv_func = estimator.predict_survival_function(
            pd.DataFrame(encode(sample, estimator, encoder)).T, return_array=False
        )[0]

        X_coverage, y_coverage = action_rule.covers(X_train, y_train)
        if len(X_coverage) < 20:
            results = pd.concat(
                [
                    results,
                    pd.DataFrame({"p": None}, index=[idx]),
                ]
            )
            continue
        time, survival_prob = kaplan_meier_estimator(
            y_coverage["cens"].astype(bool), y_coverage["time"]
        )
        recomm_surv_func = StepFunction(time, survival_prob)
        statistic, pvalue = test_diff(sample_surv_func, recomm_surv_func)
        results = pd.concat(
            [
                results,
                pd.DataFrame({"p": pvalue}, index=[idx]),
            ]
        )

    return results


def calc_significance(sample_set, mutated_sample_set, estimator, encoder, fold_path):
    results = pd.DataFrame()
    for idx, sample in sample_set.iterrows():
        sf1 = estimator.predict_survival_function(
            pd.DataFrame(encode(sample, estimator, encoder)).T, return_array=False
        )[0]
        mutated_sample = mutated_sample_set.iloc[idx]
        sf2 = estimator.predict_survival_function(
            pd.DataFrame(encode(mutated_sample, estimator, encoder)).T,
            return_array=False,
        )[0]
        statistic, pvalue = test_diff(sf1, sf2)
        results = pd.concat([results, pd.DataFrame({"p": pvalue}, index=[idx])])

    return results


def calc_coverage(recommendations, X_train, y_train):
    results = pd.DataFrame()
    for idx, action_rule in enumerate(recommendations.rules):
        X_coverage_left, _ = action_rule.covers(X_train, y_train, True)
        X_coverage_right, _ = action_rule.covers(X_train, y_train)
        results = pd.concat(
            [
                results,
                pd.DataFrame(
                    {"left": len(X_coverage_left), "right": len(X_coverage_right)},
                    index=[idx],
                ),
            ]
        )
    return results
