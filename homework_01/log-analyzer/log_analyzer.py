#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

import os.path
import sys
import typing
from argparse import ArgumentParser, FileType

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


config = {
    "REPORT_SIZE": 1000,
    "REPORT_DIR": "./reports",
    "LOG_DIR": "./log-analyzer",
    # "APP_LOG_FILE_PATH": "./resources/log_analyzer_log.log",  # - может быть загружено через внешний конфиг
}

# Сборник локальных параметров / вместо констант /
config_local = {
    "APP_DEBUG": True,
    "APP_DEBUG_LOG_FILE_PATH": "./resources/debug-log/debug_log.log",
    "APP_NAME": os.path.basename(sys.argv[0]).replace('.py', ''),
    "APP_CONFIG_DEFAULT_PATH": "./resources/config.json",
    "APP_VERSION": "0.1.20231216",
}


def first_description_print() -> None:
    """
    вывод информации при запуске
    """
    loc_prog_name = config_local.get("APP_NAME")
    loc_prog_version = config_local.get("APP_VERSION")
    print(f'{loc_prog_name} v.{loc_prog_version}',
          '- анализатор логов. Создан в рамках ДЗ-01 учебной программы OTUS.')
    return


def create_parser() -> ArgumentParser:
    """
    обработка аргументов и консольного запуска
    :return: ArgumentParser
    """
    loc_prog_name = config_local.get("APP_NAME")
    loc_prog_version = config_local.get("APP_VERSION")
    loc_config_path = config_local.get("APP_CONFIG_DEFAULT_PATH")

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

    # Нормальный режим
    if not config_local.get("APP_DEBUG"):
        loc_file_path = config.get('APP_LOG_FILE_PATH')
        loc_str = '[%(asctime)s] %(levelname).1s %(message)s'
        logging.basicConfig(
            filename=loc_file_path,
            level=logging.INFO,
            format=loc_str,
            datefmt='%Y.%m.%d%H:%M:%S'
        )

    # Режим отладки
    else:
        loc_file_path = config_local.get('APP_DEBUG_LOG_FILE_PATH')
        loc_str = "%(asctime)s ; [%(levelname)s] ; %(funcName)s ; %(lineno)d ; %(message)s"
        logging.basicConfig(
            filename=loc_file_path,
            level=logging.INFO,
            format=loc_str,
            datefmt='%Y.%m.%d%H:%M:%S',
            filemode="w"
        )
        logging.info("Log start")

    return


def get_config(config_path) -> typing.Dict:
    with open(config_path, 'r', encoding='UTF-8') as loc_file:
        config_extra = json.load(loc_file)

    result = {**config, **config_extra}

    logging.info(result)

    return result


def main():
    pass


if __name__ == "__main__":
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])

    first_description_print()

    log_init()
    current_config: typing.Dict = get_config(namespace.config.name)

    main()
