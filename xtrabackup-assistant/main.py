#!/usr/bin/env python3

import sys
from argparse import ArgumentParser

from assistant import Assistant, Command
from common import Environment
from configs import Config
from constants import TEMP_DIR_PATH
from exceptions import ConfigError
from utils import clear_dir, echo, echo_error

NAME = 'Percona XtraBackup Assistant'
VERSION = '1.0.0'
AUTHOR = 'Anton Samofal'
MIN_PYTHON_VERSION = (3, 9)


def main(command: Command):
    config = Config()
    config.print_ready_message()

    env = Environment()
    env.print_versions()

    assistant = Assistant(env, config)
    assistant.execute(command)


if __name__ == '__main__':
    if sys.version_info < MIN_PYTHON_VERSION:
        echo_error("Python %s.%s or newer is required." % MIN_PYTHON_VERSION)
        sys.exit(1)

    # register arguments for CLI
    parser = ArgumentParser(description=f"{NAME} v{VERSION}")
    parser.add_argument('--version', action='version', version=f"{NAME} v{VERSION}")
    subparsers = parser.add_subparsers(title='Available commands', required=True, dest='command')
    create_subparser = subparsers.add_parser(str(Command.CREATE), help='create database dump')
    create_subparser.add_argument(
        '--no-upload',
        action='store_true',
        help="don't upload a dump to SFTP storage",
        dest='no_upload'
    )
    subparsers.add_parser(str(Command.RESTORE), help='restore database dump')

    args = parser.parse_args()
    received_command = Command(args.command)
    if received_command is Command.CREATE and args.no_upload:
        received_command = Command.CREATE_NO_UPLOAD

    try:
        main(received_command)
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
