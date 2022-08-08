from datetime import datetime


def now(out_format: str) -> str:
    return datetime.now().strftime(out_format)
