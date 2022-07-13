#!/usr/bin/env python3

import sys
from argparse import ArgumentParser

from assistant import Environment, Assistant
from assistant.commands.command import Command
from configs import Config
from utils import rprint

# META INFO
NAME = 'Percona XtraBackup Assistant'
VERSION = 0.1
AUTHOR = 'Anton Samofal'
MIN_PYTHON_VERSION = (3, 9)


def main(command: Command):
    env = Environment()
    env.print_info()

    config = Config.from_secrets()
    assistant = Assistant(env, config)
    if command is Command.CREATE:
        assistant.create()
    elif command is Command.RESTORE:
        assistant.restore()


def parse_command() -> Command:
    """Register arguments from a command line"""
    parser = ArgumentParser(description=f"{NAME} v{VERSION}")
    parser.add_argument('--version', action='version', version=f"{NAME} v{VERSION}")

    subparsers = parser.add_subparsers(title='Available commands', required=True, dest='command')
    subparsers.add_parser(Command.CREATE.value, help='create database dump')
    subparsers.add_parser(Command.RESTORE.value, help='restore database dump')

    args = parser.parse_args()

    return Command(args.command)


if __name__ == '__main__':
    if sys.version_info < MIN_PYTHON_VERSION:
        rprint("[red]Python %s.%s or newer is required." % MIN_PYTHON_VERSION)
        sys.exit(1)

    try:
        main(parse_command())
    except RuntimeError as error:
        rprint(f"[bright_red][Error] {error}")
        sys.exit(1)
    except KeyboardInterrupt:
        print('\rTerminating...')
        sys.exit(0)
    finally:
        Assistant.clear_temp_dir()
