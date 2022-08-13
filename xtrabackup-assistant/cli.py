from argparse import ArgumentParser

from assistant import Command


class Cli:
    def __init__(self, name: str, version: str):
        self._name = name
        self._version = version

        self._parser = ArgumentParser(description=f"{self._name} v{self._version}")

    def register_arguments(self):
        self._parser.add_argument('--version', action='version', version=f"{self._parser} v{self._version}")
        subparsers = self._parser.add_subparsers(title='Available commands', required=True, dest='command')
        create_subparser = subparsers.add_parser(str(Command.CREATE), help='create database dump')
        create_subparser.add_argument(
            '--no-upload',
            action='store_true',
            help="don't upload a dump to SFTP storage",
            dest='no_upload'
        )
        subparsers.add_parser(str(Command.RESTORE), help='restore database dump')

    def get_command(self) -> Command:
        args = self._parser.parse_args()
        command = Command(args.command)
        if command is Command.CREATE and args.no_upload:
            command = Command.CREATE_NO_UPLOAD

        return command