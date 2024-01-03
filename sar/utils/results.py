import json
import os

import pandas as pd


def save_to_json(filepath, data):
    with open(filepath, "w") as fp:
        json.dump(data, fp, indent=4)


def round_dict_values(dictionary, precision):
    return {key: round(value, precision) for key, value in dictionary.items()}


def get_p_stats(df):
    return {
        0.05: len(df[df["p"] < 0.05]) / len(df),
        0.01: len(df[df["p"] < 0.01]) / len(df),
        0.005: len(df[df["p"] < 0.005]) / len(df),
        0.001: len(df[df["p"] < 0.001]) / len(df),
    }


def save_recommendations(recommendations, fold_path):
    recommendations_path = os.path.join(fold_path, "recommendations.csv")
    with open(recommendations_path, "a") as f:
        for rule in recommendations.rules:
            f.write(f"{rule.premise}\n")


def save_csv(df, fold_path, file_name):
    file_path = os.path.join(fold_path, f"{file_name}.csv")
    df.to_csv(file_path, index=True, index_label="id", float_format="%.6f")


def save_meta_table(distribution, fold_path):
    flattened_data = [
        (key, value) for key, values in distribution.dist.items() for value in values
    ]
    df = pd.DataFrame(flattened_data, columns=["attribute", "value"])
    df.to_csv(
        os.path.join(fold_path, "meta_table.csv"),
        index=False,
    )
