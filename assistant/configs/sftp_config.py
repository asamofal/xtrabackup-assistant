from dataclasses import dataclass
from pathlib import PurePath


@dataclass(frozen=True)
class SftpConfig:
    host: str
    user: str
    password: str
    path: PurePath = PurePath('/')
