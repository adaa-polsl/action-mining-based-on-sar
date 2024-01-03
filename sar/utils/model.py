from sksurv.ensemble import (
    ComponentwiseGradientBoostingSurvivalAnalysis,
    ExtraSurvivalTrees,
    GradientBoostingSurvivalAnalysis,
    RandomSurvivalForest,
)
from sksurv.linear_model import CoxnetSurvivalAnalysis


def get_model_instance(model_name, random_state):
    if model_name == "rsf":
        return RandomSurvivalForest(max_depth=2, random_state=random_state)
    elif model_name == "csa":
        return CoxnetSurvivalAnalysis(l1_ratio=0.99, fit_baseline_model=True)
    elif model_name == "est":
        return ExtraSurvivalTrees(random_state=random_state)
    elif model_name == "gbsa":
        return GradientBoostingSurvivalAnalysis(random_state=random_state)
    elif model_name == "cgbsa":
        return ComponentwiseGradientBoostingSurvivalAnalysis(random_state=random_state)
    else:
        raise ValueError(f"No model of name {model_name}")
