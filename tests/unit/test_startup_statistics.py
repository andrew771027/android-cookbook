import pytest

from android_cookbook.startup_statistics import (
    percentile,
    summarize,
)


def test_summarize_values():
    result = summarize(
        [
            100,
            200,
            300,
            400,
            500,
        ]
    )

    assert result.count == 5
    assert result.minimum == 100
    assert result.maximum == 500
    assert result.mean == 300
    assert result.median == 300
    assert result.p90 == 460
    assert result.p95 == 480
    assert result.stddev == pytest.approx(158.113883)


def test_empty_statistics():
    result = summarize([])

    assert result.count == 0
    assert result.mean is None
    assert result.median is None
    assert result.p95 is None
    assert result.stddev is None


def test_single_smaple():
    result = summarize([250])

    assert result.count == 1
    assert result.mean == 250
    assert result.median == 250
    assert result.p95 == 250
    assert result.stddev is None


def test_identical_samples():
    result = summarize(
        [
            200,
            200,
            200,
        ]
    )

    assert result.mean == 200
    assert result.stddev == 0


@pytest.mark.parametrize(
    "percent, expected",
    [
        (0, 100),
        (25, 200),
        (50, 300),
        (75, 400),
        (90, 460),
        (95, 480),
        (100, 500),
    ],
)
def test_percentile(percent, expected):
    assert percentile(
        [
            500,
            100,
            300,
            200,
            400,
        ],
        percent=percent,
    ) == pytest.approx(expected=expected)


@pytest.mark.parametrize(
    "percent",
    [
        -1,
        101,
        float("nan"),
    ],
)
def test_invalid_percentile(percent):
    with pytest.raises(ValueError):
        percentile([100, 200], percent=percent)


@pytest.mark.parametrize(
    "values",
    [
        [-1, 100],
        [float("nan")],
        [float("inf")],
        [float("-inf")],
    ],
)
def test_invalid_timing_values(values):
    with pytest.raises(ValueError):
        summarize(values)


def test_empty_percentile():
    with pytest.raises(ValueError):
        percentile([], 95)


def test_input_order_is_preserved():
    values = [
        300,
        100,
        200,
    ]

    summarize(values)

    assert values == [
        300,
        100,
        200,
    ]
