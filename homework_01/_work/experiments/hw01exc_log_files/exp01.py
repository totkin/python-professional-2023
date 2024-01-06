import os
import sys
from argparse import ArgumentParser, FileType

version = "1.2.1"

def create_parser(prog_name: str | None = os.path.basename(__file__)) -> ArgumentParser:
    parser: ArgumentParser = ArgumentParser(
        prog=prog_name,
        description='''Анализатор логов. В рамках ДЗ-01 учебной программы OTUS.''',
        epilog='''(c) T for Otus 2023. Применение ограничено рамками учебной задачи.''',
        add_help=False
    )
    argument_group = parser.add_argument_group(title='Параметры')
    argument_group.add_argument('--help', '-h', action='help', help='Справка')
    argument_group.add_argument('-c', '--config_file_name',
                                type=FileType(),
                                # metavar='CONFIG',
                                help='Необязательный параметр. Файл конфигурации.')
    argument_group.add_argument('--version',
                                action='version',
                                help='Вывести номер версии',
                                version='%(prog)s {}'.format(version))
    return parser


if __name__ == '__main__':
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])

    print("Привет, {}!".format(namespace.config_file_name))
