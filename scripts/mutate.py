import rootutils
import datetime
import os
import sys
import hydra
import logging
from omegaconf import DictConfig, OmegaConf

import pandas as pd
import warnings

warnings.simplefilter(action="ignore", category=FutureWarning)

sys.path.append(os.path.abspath("."))

from sar.actions import (
    ActionMetaTable,
    ActionRangeDistribution,
    OptimizedActionMetaTable,
)
from sar.utils.model import get_model_instance
from sar.utils.mutator import Mutator
from sar.utils.processing import encode_features, encode_target, impute_missing_values
from sar.utils.results import (
    get_p_stats,
    round_dict_values,
    save_csv,
    save_meta_table,
    save_recommendations,
    save_to_json,
)
from sar.utils.rules import read_rules
from sar.utils.stats import calc_diff, calc_significance, calc_coverage

rootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)

log = logging.getLogger(__name__)


COVERED_EXAMPLES_FILENAME = "coveredExamples.txt"
EACH_RULE_STATISTIC_FILENAME = "eachRuleStatistic.csv"
ESTIMATOR_FILENAME = "estimator.csv"
RULE_FILENAME = "result.txt"

PRECISION = 6

from scipy.io import arff
import xml.etree.ElementTree as ET


def read_arff(path: str) -> pd.DataFrame:
    data_df = pd.DataFrame(arff.loadarff(open(path, "r", encoding="cp1252"))[0])
    # code to fix the problem with encoding of the file
    tmp_df = data_df.select_dtypes([object])
    if tmp_df.shape[1] != 0:
        tmp_df = tmp_df.stack().str.decode("cp1252").unstack()
        for col in tmp_df:
            data_df[col] = tmp_df[col]
    data_df = data_df.replace({"?": None})

    data_df = data_df.replace(
        {
            "Worst isn\\t moderate'": "Worst isn't moderate",
            "Worst isn\\t mild'": "Worst isn't mild",
            "Worst isn\\t severe'": "Worst isn't severe",
        },
        regex=False,
    )

    return data_df


def get_stable_attributes(xml_path, dataset_name, fold_number):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    stable_attributes = []

    for dataset in root.find("datasets").findall("dataset"):
        out_directory = dataset.find("out_directory").text
        if f"{dataset_name}/{fold_number}" in out_directory:
            stable_attrs_element = dataset.find("stable_attributes")
            if stable_attrs_element is not None:
                stable_attributes = [
                    attr.text
                    for attr in stable_attrs_element.findall("stable_attribute")
                ]
            else:
                return None
            break

    return stable_attributes


def process_fold(cfg: DictConfig):
    log.debug(f"{cfg.dataset} {cfg.fold}")
    log.info(f"{cfg.dataset} {cfg.fold}")

    log.info(f"datasets and rules reading and processing...")
    fold_dir_path = os.path.join(cfg.paths.data_dir, cfg.dataset, str(cfg.fold))
    train_dataset_path = os.path.join(fold_dir_path, "train.arff")
    test_dataset_path = os.path.join(fold_dir_path, "test.arff")
    df_train_raw = read_arff(train_dataset_path)
    df_test_raw = read_arff(test_dataset_path)

    df_train = impute_missing_values(df_train_raw)
    df_test = impute_missing_values(df_test_raw)

    y_train = encode_target(df_train)
    df_raw = pd.concat([df_train, df_test]).reset_index(drop=True)
    X, X_encoded, encoder = encode_features(df_raw)
    X_train = X.iloc[: len(df_train)].reset_index(drop=True)
    X_test = X.iloc[-len(df_test) :].reset_index(drop=True)

    X_train_encoded = X_encoded.iloc[: len(df_train)]
    estimator = get_model_instance(cfg.model, random_state=cfg.random_state).fit(
        X_train_encoded, y_train
    )

    ruleset_dir = os.path.join(cfg.paths.rules_dir, cfg.ruleset)
    rule_file_path = os.path.join(
        ruleset_dir, cfg.dataset, str(cfg.fold), "any-target-rule", RULE_FILENAME
    )
    rules = read_rules(rule_file_path)
    if len(rules) == 0:
        print(f"no rules for dataset {cfg.dataset}")
        return

    log.info(f"action distribution calculation...")
    distribution = ActionRangeDistribution(rules, X_train, y_train)
    distribution.calculate_action_distribution()
    measure = None
    stable_attributes = get_stable_attributes(
        cfg.paths.config_path, cfg.dataset, cfg.fold
    )
    meta_table: ActionMetaTable = OptimizedActionMetaTable(
        distribution,
        measure,
        stable_attributes,
        cfg.target,
        cfg.method,
        estimator,
        encoder,
    )

    source_examples_in_test_set: pd.DataFrame = (
        X_test.copy() if cfg.test else X_train.copy()
    )

    log.info(f"example mutation...")
    test_set_mutated_by_recommendations: pd.DataFrame
    test_set_mutated_by_recommendations, recommendations = Mutator().mutate_examples(
        source_examples_in_test_set, meta_table, X_train
    )

    log.info(f"significance calculation...")
    # KM comparison for examples before and after modifications where KMs are calculated by an external boosting model
    significance = calc_significance(
        source_examples_in_test_set,
        test_set_mutated_by_recommendations,
        estimator,
        encoder,
        cfg.paths.output_dir,
    )
    log.info(f"diff calculation...")
    # comparison of the KM of the right rules with the KM generated by the boosting model
    diff = calc_diff(
        test_set_mutated_by_recommendations,
        recommendations,
        X_train,
        y_train,
        estimator,
        encoder,
        cfg.paths.output_dir,
    )

    log.info(f"coverage calculation...")
    coverage = calc_coverage(recommendations, X_train, y_train)

    log.info(f"stats calculation...")
    mutation_stats = Mutator().calculate_stats(
        source_examples_in_test_set, test_set_mutated_by_recommendations, X_train
    )

    log.info(f"results saving...")
    save_csv(coverage, cfg.paths.output_dir, "coverage")
    save_csv(df_train_raw, cfg.paths.output_dir, "train_set")
    save_csv(df_test_raw, cfg.paths.output_dir, "test_set")
    save_csv(
        test_set_mutated_by_recommendations, cfg.paths.output_dir, "test_set_mutated"
    )
    save_csv(mutation_stats, cfg.paths.output_dir, "mutation_stats")
    save_csv(significance, cfg.paths.output_dir, "significance")
    save_csv(diff, cfg.paths.output_dir, "diff")

    save_meta_table(distribution, cfg.paths.output_dir)
    save_recommendations(recommendations, cfg.paths.output_dir)

    # save aggregated diff and significance
    diff_stats = round_dict_values(get_p_stats(diff), 6)
    save_to_json(os.path.join(cfg.paths.output_dir, "diff_stats.json"), diff_stats)
    significance_stats = round_dict_values(get_p_stats(significance), 6)
    save_to_json(
        os.path.join(cfg.paths.output_dir, "significance_stats.json"),
        significance_stats,
    )

    mutation_stats_mean = {
        "distance": mutation_stats["distance"].mean(),
        "n_actions": mutation_stats["n_actions"].mean(),
    }
    mutation_stats_mean = round_dict_values(mutation_stats_mean, 6)
    save_to_json(
        os.path.join(cfg.paths.output_dir, "mutation_stats_mean.json"),
        mutation_stats_mean,
    )


@hydra.main(version_base=None, config_path="../conf", config_name="mutate")
def main(cfg: DictConfig):
    process_fold(cfg)


if __name__ == "__main__":
    main()
