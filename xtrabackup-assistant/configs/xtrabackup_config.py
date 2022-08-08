from dataclasses import dataclass


@dataclass(frozen=True)
class XtrabackupConfig:
    user: str
    password: str
    parallel: int = 10
