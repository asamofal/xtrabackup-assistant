from typing import Union

from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.table import Table
from rich.text import Text

from utils import now

rprint = Console(highlight=False).print


def echo(
    text: Union[str, Text, Panel, Table],
    author: Union[str, None] = 'Assistant',
    style: Union[str, Style] = 'default',
    time: bool = True
) -> None:
    if isinstance(text, (Panel, Table)):
        rprint(text)
    else:
        message = Text()

        if author:
            message.append(f'[{author}] ', 'blue')

        if time:
            message.append(Text(f"[{now('%Y-%m-%d %H:%M:%S')}] ", 'default'))

        text = text if isinstance(text, Text) else Text.from_markup(str(text), style=style)
        message.append_text(text)

        rprint(message)


def echo_error(text: Union[str, Text, Panel, Exception], author: str = 'Error') -> None:
    message = Text(f'[{author}] ', 'bright_red')
    text = text if isinstance(text, Text) else Text.from_markup(str(text))
    message.append_text(text)

    echo(message, author=None, time=False)


def echo_warning(text: Union[str, Text, Panel, Exception], author: str = 'Error') -> None:
    message = Text(f'[{author}] ', 'dark_orange')
    text = text if isinstance(text, Text) else Text.from_markup(str(text))
    message.append_text(text)

    echo(message, author=None, time=False)
