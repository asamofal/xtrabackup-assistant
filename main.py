#!/usr/bin/env python3

import sys
from argparse import ArgumentParser

from assistant import Environment, Assistant
from assistant.commands.command import Command
from assistant.configs import Config
from errors import ConfigError
from utils import rprint
from utils.slack import Slack

NAME = 'Percona XtraBackup Assistant'
VERSION = '1.0.0'
AUTHOR = 'Anton Samofal'
MIN_PYTHON_VERSION = (3, 9)


def main(command: Command):
    config = Config()
    config.print_ready_message()

    try:
        env = Environment()
        env.print_versions()

        assistant = Assistant(env, config)
        assistant.execute(command)
    except RuntimeError as e:
        if config.slack is not None:
            Slack(config.slack).notify(project=config.project, error=e)
        raise RuntimeError(e)


if __name__ == '__main__':
    if sys.version_info < MIN_PYTHON_VERSION:
        rprint("[red]Python %s.%s or newer is required." % MIN_PYTHON_VERSION)
        sys.exit(1)

    # register arguments from a command line
    parser = ArgumentParser(description=f"{NAME} v{VERSION}")
    parser.add_argument('--version', action='version', version=f"{NAME} v{VERSION}")
    subparsers = parser.add_subparsers(title='Available commands', required=True, dest='command')
    subparsers.add_parser(Command.CREATE.value, help='create database dump')
    subparsers.add_parser(Command.RESTORE.value, help='restore database dump')

    received_command = Command(parser.parse_args().command)

    try:
        main(received_command)
    except ConfigError as error:
        rprint(f"[bright_red][Config] {error}")
        sys.exit(1)
    except RuntimeError as error:
        rprint(f"[bright_red][Error] {error}")
        sys.exit(1)
    except KeyboardInterrupt:
        print('\rTerminating...')
        sys.exit()
    finally:
        Assistant.clear_temp_dir()
