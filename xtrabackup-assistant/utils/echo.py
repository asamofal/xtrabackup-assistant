from typing import Union

from rich.panel import Panel
from rich.style import Style
from rich.text import Text

from utils import rprint, now


def echo(
    text: Union[str, Text, Panel],
    author: str = 'Assistant',
    style: Union[str, Style] = 'default',
    time: bool = True
) -> None:
    if isinstance(text, Panel):
        rprint(text)
    else:
        message = Text()

        if author:
            message.append(f'[{author}] ', 'blue')

        if time:
            message.append(Text(f"[{now('%Y-%m-%d %H:%M:%S')}] ", 'default'))

        text = text if isinstance(text, Text) else Text(text, style)
        message.append(text)

        rprint(message)
