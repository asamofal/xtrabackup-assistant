from dataclasses import dataclass


@dataclass(frozen=True)
class SftpConfig:
    host: str
    user: str
    password: str
    path: str = '/'
