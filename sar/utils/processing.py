import numpy as np
import numpy.lib.recfunctions as rfn
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder


def encode_features(df):
    X = df.drop(columns=["survival_time", "survival_status"])
    obj_cols = X.select_dtypes(["object"]).columns
    if len(obj_cols) == 0:
        return X, X, None
    else:
        enc = OneHotEncoder(sparse_output=False, drop="first")
        encoded_array = enc.fit_transform(X.loc[:, obj_cols])
        df_encoded = pd.DataFrame(encoded_array, columns=enc.get_feature_names_out())
        df_sklearn_encoded = pd.concat([X, df_encoded], axis=1)
        df_sklearn_encoded.drop(labels=obj_cols, axis=1, inplace=True)

        return X, df_sklearn_encoded, enc


def encode_target(df, status_label="cens", time_label="time"):
    y = df[["survival_status", "survival_time"]].copy()
    y["survival_status"] = y["survival_status"].astype(bool)
    y = y.to_records(index=False)
    y = rfn.rename_fields(
        y, {"survival_status": status_label, "survival_time": time_label}
    )
    return y


def impute_missing_values(df):
    df = df.fillna(value=np.nan)
    df[:] = SimpleImputer(strategy="most_frequent").fit_transform(df)
    return df


def encode(sample: pd.Series, estimator, encoder) -> pd.Series:
    if encoder == None:
        return sample
    all_cols = list(sample.index)
    nominal_cols = encoder.feature_names_in_
    if len(nominal_cols) == 0:
        return sample
    numeric_cols = list(set(all_cols) - set(nominal_cols))
    sample_nominal = sample.loc[nominal_cols]
    sample_numeric = sample.loc[numeric_cols]
    sample_nominal_transformed_vals = encoder.transform(pd.DataFrame(sample_nominal).T)[
        0
    ]
    nominal_cols_transformed = encoder.get_feature_names_out()
    current_sample_numeric_transformed = pd.Series(
        sample_nominal_transformed_vals,
        index=nominal_cols_transformed,
        name=sample.name,
    )
    sample_transformed = pd.concat(
        [sample_numeric, current_sample_numeric_transformed], axis=0, join="inner"
    )
    return sample_transformed.reindex(estimator.feature_names_in_)
