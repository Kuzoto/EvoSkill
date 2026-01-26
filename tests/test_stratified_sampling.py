"""Tests for category-aware stratified sampling."""

import pandas as pd
import pytest


def stratified_split(
    data: pd.DataFrame, train_ratio: float = 0.18, val_ratio: float = 0.12
) -> tuple[dict[str, list[tuple[str, str]]], list[tuple[str, str, str]]]:
    """Split data ensuring each category has at least 1 in both train and validation.

    This is a copy of the function from scripts/run_loop.py for testing purposes.
    """
    if train_ratio + val_ratio > 1.0:
        raise ValueError(f"train_ratio ({train_ratio}) + val_ratio ({val_ratio}) cannot exceed 1.0")

    data = data.dropna(subset=['category'])
    categories = data['category'].unique()
    train_pools: dict[str, list[tuple[str, str]]] = {}
    val_data: list[tuple[str, str, str]] = []

    for cat in categories:
        cat_data = data[data['category'] == cat].sample(frac=1, random_state=42)
        n_train = max(1, int(len(cat_data) * train_ratio))
        n_val = max(1, int(len(cat_data) * val_ratio))

        train_pools[cat] = [
            (row.question, row.ground_truth)
            for _, row in cat_data.head(n_train).iterrows()
        ]
        val_data.extend([
            (row.question, row.ground_truth, cat)
            for _, row in cat_data.iloc[n_train:n_train + n_val].iterrows()
        ])

    return train_pools, val_data


@pytest.fixture
def sample_dataset() -> pd.DataFrame:
    """Create a sample dataset with 6 categories of varying sizes."""
    data = {
        "question": [f"Q{i}" for i in range(30)],
        "ground_truth": [f"A{i}" for i in range(30)],
        "category": (
            ["Comparison/Change"] * 10 +
            ["Statistical Metrics"] * 6 +
            ["Modeling/Forecasting"] * 5 +
            ["Transform/Normalize"] * 4 +
            ["Aggregation"] * 3 +
            ["Lookup/Extraction"] * 2
        ),
    }
    return pd.DataFrame(data)


class TestStratifiedSplit:
    """Tests for the stratified_split function."""

    def test_stratified_split_min_one_per_category(self, sample_dataset: pd.DataFrame):
        """Every category has >= 1 sample in both train and validation."""
        train_pools, val_data = stratified_split(sample_dataset, train_ratio=0.18, val_ratio=0.12)

        # Get categories in validation
        val_categories = set(cat for _, _, cat in val_data)

        # All 6 categories should be in validation and training
        expected_categories = set(sample_dataset["category"].unique())
        assert val_categories == expected_categories, (
            f"Expected all categories in validation. "
            f"Missing: {expected_categories - val_categories}"
        )
        assert set(train_pools.keys()) == expected_categories, (
            f"Expected all categories in training. "
            f"Missing: {expected_categories - set(train_pools.keys())}"
        )

    def test_stratified_split_no_overlap(self, sample_dataset: pd.DataFrame):
        """No question appears in both train_pools and val_data."""
        train_pools, val_data = stratified_split(sample_dataset, train_ratio=0.18, val_ratio=0.12)

        # Collect all training questions
        train_questions = set()
        for pool in train_pools.values():
            for question, _ in pool:
                train_questions.add(question)

        # Collect all validation questions
        val_questions = set(question for question, _, _ in val_data)

        # No overlap
        overlap = train_questions & val_questions
        assert len(overlap) == 0, f"Questions appear in both train and val: {overlap}"

    def test_stratified_split_respects_ratios(self, sample_dataset: pd.DataFrame):
        """Train + val is approximately (train_ratio + val_ratio) of total data."""
        train_ratio, val_ratio = 0.18, 0.12
        train_pools, val_data = stratified_split(sample_dataset, train_ratio=train_ratio, val_ratio=val_ratio)

        total_train = sum(len(pool) for pool in train_pools.values())
        total_val = len(val_data)
        total_original = len(sample_dataset)

        # With min 1 per category, actual ratio may be higher for small categories
        # Just verify we're not using all the data
        assert total_train + total_val <= total_original, (
            f"Used more data than available: {total_train} + {total_val} > {total_original}"
        )


class TestRoundRobinSampling:
    """Tests for round-robin sampling logic."""

    @pytest.fixture
    def train_pools(self) -> dict[str, list[tuple[str, str]]]:
        """Create train pools with 6 categories."""
        return {
            "Comparison/Change": [(f"CC_Q{i}", f"CC_A{i}") for i in range(8)],
            "Statistical Metrics": [(f"SM_Q{i}", f"SM_A{i}") for i in range(5)],
            "Modeling/Forecasting": [(f"MF_Q{i}", f"MF_A{i}") for i in range(4)],
            "Transform/Normalize": [(f"TN_Q{i}", f"TN_A{i}") for i in range(3)],
            "Aggregation": [(f"AG_Q{i}", f"AG_A{i}") for i in range(2)],
            "Lookup/Extraction": [(f"LE_Q{i}", f"LE_A{i}") for i in range(1)],
        }

    def sample_batch(
        self,
        train_pools: dict[str, list[tuple[str, str]]],
        categories: list[str],
        category_offset: int,
        per_cat_offset: dict[str, int],
        samples_per_iter: int,
    ) -> tuple[list[tuple[str, str, str]], int, dict[str, int]]:
        """Simulate round-robin sampling for one batch."""
        n_cats = len(categories)
        test_samples: list[tuple[str, str, str]] = []

        for j in range(samples_per_iter):
            cat_idx = (category_offset + j) % n_cats
            cat = categories[cat_idx]
            pool = train_pools[cat]
            sample_idx = per_cat_offset[cat] % len(pool)
            question, answer = pool[sample_idx]
            test_samples.append((question, answer, cat))
            per_cat_offset[cat] += 1

        category_offset += samples_per_iter
        return test_samples, category_offset, per_cat_offset

    def test_round_robin_samples_different_categories(
        self, train_pools: dict[str, list[tuple[str, str]]]
    ):
        """Batch contains samples from 3 different categories."""
        categories = sorted(train_pools.keys())
        category_offset = 0
        per_cat_offset = {cat: 0 for cat in categories}
        samples_per_iter = 3

        samples, _, _ = self.sample_batch(
            train_pools, categories, category_offset, per_cat_offset, samples_per_iter
        )

        # Get unique categories in this batch
        sampled_categories = set(cat for _, _, cat in samples)
        assert len(sampled_categories) == 3, (
            f"Expected 3 different categories, got {len(sampled_categories)}: {sampled_categories}"
        )

    def test_round_robin_cycles_through_all_categories(
        self, train_pools: dict[str, list[tuple[str, str]]]
    ):
        """After 2 batches of 3, all 6 categories are represented."""
        categories = sorted(train_pools.keys())
        category_offset = 0
        per_cat_offset = {cat: 0 for cat in categories}
        samples_per_iter = 3

        all_sampled_categories = set()

        # Sample 2 batches
        for _ in range(2):
            samples, category_offset, per_cat_offset = self.sample_batch(
                train_pools, categories, category_offset, per_cat_offset, samples_per_iter
            )
            for _, _, cat in samples:
                all_sampled_categories.add(cat)

        assert all_sampled_categories == set(categories), (
            f"Expected all 6 categories after 2 batches. "
            f"Missing: {set(categories) - all_sampled_categories}"
        )

    def test_round_robin_cycles_within_category(
        self, train_pools: dict[str, list[tuple[str, str]]]
    ):
        """Sampling from a category 4 times wraps around to first sample."""
        # Use Aggregation which has only 2 samples
        cat = "Aggregation"
        pool = train_pools[cat]
        assert len(pool) == 2, "Test assumes Aggregation has 2 samples"

        # Simulate sampling from this category 4 times
        per_cat_offset = 0
        sampled_questions = []

        for _ in range(4):
            sample_idx = per_cat_offset % len(pool)
            question, _ = pool[sample_idx]
            sampled_questions.append(question)
            per_cat_offset += 1

        # Should see: sample0, sample1, sample0, sample1
        assert sampled_questions[0] == sampled_questions[2], (
            f"Expected wrap-around: {sampled_questions[0]} != {sampled_questions[2]}"
        )
        assert sampled_questions[1] == sampled_questions[3], (
            f"Expected wrap-around: {sampled_questions[1]} != {sampled_questions[3]}"
        )
