import pandas as pd
import logging
from pandas.api.types import is_numeric_dtype

from sar.actions import ActionMetaTable, MetaAnalysisResult
from sar.representation import Action, ActionRule, ActionRuleSet, AnyValueSet

NOMINAL_ACTION_MUTATION_COST = 1

log = logging.getLogger(__name__)


class Mutator:
    def mutate_examples(self, test_X, metaTable: ActionMetaTable, train_set):
        used_recommendations = ActionRuleSet()
        mutated: pd.Series = None
        failedCount = 0
        test_X_mutated = pd.DataFrame()

        for _, current_sample in test_X.iterrows():
            recommendations: list[MetaAnalysisResult] = metaTable.analyze(
                current_sample, True, False
            )
            if not recommendations:
                failedCount += 1
                continue
            golden: MetaAnalysisResult = recommendations[0]
            as_rule: ActionRule = golden.get_action_rule()

            used_recommendations.add_rule(as_rule)
            mutated_sample = current_sample.copy()
            for action in as_rule.premise.subconditions:
                attribute_to_mutate: str = action.attribute

                if is_numeric_dtype(test_X[attribute_to_mutate]):
                    mutated_sample = self.mutate_numerical_attribute(
                        mutated_sample, attribute_to_mutate, action, train_set
                    )
                else:
                    mutated_sample = self.mutate_nominal_attribute(
                        mutated_sample, attribute_to_mutate, action
                    )

            test_X_mutated = pd.concat(
                [test_X_mutated, pd.DataFrame(mutated_sample).T], axis=0
            )

        log.debug("Failed to mutate by recoms " + str(failedCount) + " examples")
        return test_X_mutated, used_recommendations

    def mutate_sample(self, sample, meta_example, train_set):
        if meta_example.data == {}:
            return sample

        mutated_sample = sample.copy()
        for attribute_to_mutate, meta_value in meta_example.data.items():
            action = Action(attribute_to_mutate, None, meta_value.value)
            if is_numeric_dtype(train_set[attribute_to_mutate]):
                mutated_sample = self.mutate_numerical_attribute(
                    mutated_sample, attribute_to_mutate, action, train_set
                )
            else:
                mutated_sample = self.mutate_nominal_attribute(
                    mutated_sample, attribute_to_mutate, action
                )
        return mutated_sample

    def mutate_nominal_attribute(
        self,
        to_be_mutated: pd.Series,
        attribute_to_mutate: str,
        suggested_mutation: Action,
    ) -> Action:
        if suggested_mutation.right_value == None:
            return to_be_mutated

        if isinstance(suggested_mutation.right_value.value_set, AnyValueSet):
            return to_be_mutated
        else:
            new_value = suggested_mutation.right_value.value_set.value
            to_be_mutated[attribute_to_mutate] = new_value
            return to_be_mutated

    def mutate_numerical_attribute(
        self,
        to_be_mutated: pd.Series,
        attribute_to_mutate: str,
        suggested_mutation: Action,
        X_train,
    ) -> Action:
        if suggested_mutation.right_value == None:
            return to_be_mutated
        left = (
            X_train[attribute_to_mutate].min()
            if suggested_mutation.right_value.value_set.left == float("-inf")
            else suggested_mutation.right_value.value_set.left
        )
        right = (
            X_train[attribute_to_mutate].max()
            if suggested_mutation.right_value.value_set.right == float("inf")
            else suggested_mutation.right_value.value_set.right
        )
        X_train_filtered = X_train[
            (left <= X_train[attribute_to_mutate])
            & (X_train[attribute_to_mutate] <= right)
        ]
        if len(X_train_filtered) == 0:
            new_value = (left + right) / 2
        else:
            new_value = X_train_filtered[attribute_to_mutate].median()

        to_be_mutated[attribute_to_mutate] = new_value

        return to_be_mutated

    def calculate_stats(
        self,
        source_examples_in_test_set: pd.DataFrame,
        test_set_mutated_by_recommendations: pd.DataFrame,
        train_set: pd.DataFrame,
    ) -> pd.DataFrame:
        mutation_stats = pd.DataFrame(columns=["distance", "n_actions"])
        for idx, mutated_sample in test_set_mutated_by_recommendations.iterrows():
            source_sample = source_examples_in_test_set.loc[idx]
            mutated_attributes: list[str] = self.get_mutated_attributes(
                mutated_sample, source_sample
            )
            total_distance: float = self.calculate_distance(
                mutated_sample, source_sample, mutated_attributes, train_set
            )
            n_actions: int = self.calculate_n_actions(mutated_sample, source_sample)
            mutation_stat = {"distance": total_distance, "n_actions": n_actions}
            mutation_stats = pd.concat(
                [mutation_stats, pd.DataFrame([mutation_stat])], ignore_index=True
            )
        return mutation_stats

    def get_mutated_attributes(
        self, mutated_sample: pd.Series, source_sample: pd.Series
    ) -> list[str]:
        comparison = mutated_sample.compare(
            source_sample, keep_shape=True, keep_equal=True
        )
        comparison_equal = comparison["self"] == comparison["other"]
        if False in comparison_equal.value_counts().index:
            return list(comparison_equal[comparison_equal == False].index)
        else:
            return []

    def calculate_n_actions(
        self, mutated_sample: pd.Series, source_sample: pd.Series
    ) -> int:
        comparison = mutated_sample.compare(
            source_sample, keep_shape=True, keep_equal=True
        )
        comparison["equal"] = comparison["self"] == comparison["other"]
        if False in comparison["equal"].value_counts().index:
            return int(comparison["equal"].value_counts()[False])
        else:
            return 0

    def calculate_distance(
        self,
        mutated_sample: pd.Series,
        new_sample_copy: pd.Series,
        mutated_attributes: list[str],
        train_set,
    ) -> float:
        total_distance = 0
        for attribute in mutated_attributes:
            if is_numeric_dtype(train_set[attribute]):
                change = abs(mutated_sample[attribute] - new_sample_copy[attribute])
                attribute_distance = change / abs(
                    train_set[attribute].max() - train_set[attribute].min()
                )
                total_distance += attribute_distance
            else:
                total_distance += NOMINAL_ACTION_MUTATION_COST
        return float(total_distance) / len(train_set.columns)
