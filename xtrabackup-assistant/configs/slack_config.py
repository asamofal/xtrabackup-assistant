from dataclasses import dataclass


@dataclass(frozen=True)
class SlackConfig:
    token: str
    channel: str
