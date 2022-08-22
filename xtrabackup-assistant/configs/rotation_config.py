from dataclasses import dataclass


@dataclass(frozen=True)
class RotationConfig:
    max_store_time_years: int
    keep_for_last_days: int
