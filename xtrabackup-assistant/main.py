#!/usr/bin/env python3

import sys

from assistant import Assistant, Command
from cli import Cli
from configs import Config
from constants import TEMP_DIR_PATH
from exceptions import ConfigError
from utils import clear_dir, echo, echo_error

NAME = 'Percona XtraBackup Assistant'
VERSION = '1.0.4'
AUTHOR = 'Anton Samofal'
MIN_PYTHON_VERSION = (3, 9)


def main(command: Command):
    config = Config()
    config.print_ready_message()

    assistant = Assistant(config)
    assistant.execute(command)


if __name__ == '__main__':
    if sys.version_info < MIN_PYTHON_VERSION:
        echo_error("Python %s.%s or newer is required." % MIN_PYTHON_VERSION)
        sys.exit(1)

    cli = Cli(NAME, VERSION)
    cli.register_arguments()

    try:
        main(cli.get_command())
    except ConfigError as error:
        echo_error(error, 'Config')
        sys.exit(1)
    except RuntimeError as error:
        echo_error(error)
        sys.exit(1)
    except KeyboardInterrupt:
        echo('\rTerminating...', author=None, time=False)
        sys.exit()
    finally:
        clear_dir(TEMP_DIR_PATH)
