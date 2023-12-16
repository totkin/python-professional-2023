#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import sys
from argparse import ArgumentParser, FileType

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log-analyzer",
}

config_local = {
    "PROGRAMM_NAME": os.path.basename(sys.argv[0]).replace('.py', ''),
    "PROGRAMM_VERSION": "0.1.20231216",
    "CONFIG_DEFAULT_PATH": './resources/config.json',
}


def create_parser(prog_name: str = None) -> ArgumentParser:
    loc_prog_name = config_local.get("PROGRAMM_NAME")
    loc_prog_version = config_local.get("PROGRAMM_VERSION")
    loc_config_path = config_local.get("CONFIG_DEFAULT_PATH")

    parser: ArgumentParser = ArgumentParser(
        description=f'{loc_prog_name} - анализатор логов. Создан в рамках ДЗ-01 учебной программы OTUS.',
        epilog='(c) T for Otus 2023. Применение ограничено рамками учебной задачи.',
        add_help=False,
    )
    arg_group = parser.add_argument_group(title='Параметры')
    arg_group.add_argument('-c', '--config',
                           type=FileType(),
                           metavar='',
                           help=f'Файл конфигурации. По-умолчанию это {loc_config_path}',
                           default=loc_config_path,
                           )
    arg_group.add_argument('-v', '--version',
                           action='version',
                           help='Номер версии',
                           version=f'{loc_prog_name} v.{loc_prog_version}')
    arg_group.add_argument('-h', '--help', action='help', help='Справка')

    return parser


def log_init():
    loc_file_path = config.get('LOG_FILE_PATH')

    logging.basicConfig(
        filename=loc_file_path,
        level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d%H:%M:%S'
    )
    return


def first_description_print():
    loc_prog_name = config_local.get("PROGRAMM_NAME")
    loc_prog_version = config_local.get("PROGRAMM_VERSION")
    print(f'{loc_prog_name} v.{loc_prog_version}',
          '- анализатор логов. Создан в рамках ДЗ-01 учебной программы OTUS.')
    return


def main():
    pass


if __name__ == "__main__":
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])
    first_description_print()

    # добавить в конфиг LOG_FILE_PATH
    log_init()
    main()
