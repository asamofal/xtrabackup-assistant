#!/usr/bin/env python3

import sys
from argparse import ArgumentParser
from colorama import Fore as Color, Style, init as colorama_init

NAME = 'Percona XtraBackup assistant'
VERSION = 0.1
MIN_PYTHON_VERSION = (3, 10, 4)
AUTHOR = 'Anton Samofal'


def parse_command():
    """Parse arguments from a command line"""
    parser = ArgumentParser(description=f"Percona XtraBackup assistant v{VERSION}")
    parser.add_argument('--version', action='version', version=f"{NAME} v{VERSION}")

    subparsers = parser.add_subparsers(title='Available commands', required=True, dest='command')
    subparsers.add_parser('create', help='create database dump')
    subparsers.add_parser('restore', help='restore database dump')

    return parser.parse_args()


def main():
    print(f"{Color.GREEN}{Style.BRIGHT}Percona XtraBackup assistant [v{ VERSION}]{Style.RESET_ALL}{Color.RESET}")

    match command:
        case 'create':
            print('create')
        case 'import':
            print('restore')


if __name__ == '__main__':
    if sys.version_info < MIN_PYTHON_VERSION:
        sys.exit(f"{Color.RED}Python %s.%s.%s or newer is required.{Color.RESET}" % MIN_PYTHON_VERSION)

    # init colorama module
    colorama_init(autoreset=True)

    command = parse_command()

    try:
        main()
    except KeyboardInterrupt:
        print('')
        sys.exit(0)
