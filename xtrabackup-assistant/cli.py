from argparse import ArgumentParser

from assistant import Command


class Cli:
    def __init__(self, name: str, version: str):
        self._name = name
        self._version = version

        self._parser = ArgumentParser(description=f"{self._name} v{self._version}")

    def register_arguments(self):
        self._parser.add_argument('--version', action='version', version=f"{self._name} v{self._version}")

        subparsers = self._parser.add_subparsers(title='Available commands', required=True, dest='command')
        create_subparser = subparsers.add_parser(str(Command.CREATE), help='create database dump')
        create_subparser.add_argument(
            '--upload',
            action='store_true',
            help="upload a dump to SFTP storage",
            dest='upload'
        )

        subparsers.add_parser(str(Command.RESTORE), help='restore database dump')
        subparsers.add_parser(str(Command.ROTATE), help='rotate backups (remove old)')

    def get_command(self) -> Command:
        args = self._parser.parse_args()
        command = Command(args.command)
        if command is Command.CREATE and args.upload:
            command = Command.CREATE_UPLOAD

        return command
