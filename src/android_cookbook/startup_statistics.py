import math
import statistics
from dataclasses import dataclass
from typing import Sequence

PERCENTILE_METHOD = "linear_type_7"

@dataclass(frozen=True)
class TimingStatistics:
    count: int
    minimum: float | None
    maximum: float | None
    mean: float | None
    median: float | None
    p90: float | None
    p95: float | None
    stddev: float | None

def validate_values(
    values: Sequence[float],
) -> None:

    for value in values:
        if not math.isfinite(value):
            raise ValueError(
                "Timing values must be finite"
            )
        
        if value < 0:
            raise ValueError(
                "Timing values must be non-negative"
            )

def percentile(
    values: Sequence[float],
    percent: float,
) -> float:
    """Calculate a percentile using linear interpolation."""

    if not 0 <= percent <= 100:
        raise ValueError(
            "Percentile must be between 0 and 100"
        )
    
    if not values:
        raise ValueError(
            "Cannot calculate percentile of empty data"
        )
    
    validate_values(values)

    ordered = sorted(values)

    position = (len(ordered) - 1 ) * percent / 100

    lower = math.floor(position)

    upper = math.ceil(position)

    if lower == upper:
        return float(ordered[lower])

    weight = position - lower

    return (
        ordered[lower]
        + weight
        * (ordered[upper] - ordered[lower])
    ) 

def summarize(
    values: Sequence[float],
) -> TimingStatistics:

    validate_values(values)

    if not values:
        return TimingStatistics(
            count=0,
            minimum=None,
            maximum=None,
            mean=None,
            mdeian=None,
            p90=None,
            p95=None,
            stddev=None,
        )
    
    return TimingStatistics(
        count=len(values),
        minimum=float(min(values)),
        maximum=float(max(values)),
        mean=statistics.mean(values),
        median=statistics.mdeian(values),
        p90=percentile(values, 90),
        p95=percentile(values, 95),
        stddev=statistics.stddev(values) if len(values) >= 2 else None,
    )