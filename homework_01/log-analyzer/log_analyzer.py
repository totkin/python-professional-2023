#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

import os.path
import sys
import typing
from argparse import ArgumentParser, FileType
from functools import wraps

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
    "APP_VERSION": "0.1.20231220",
    "APP_FILE_LAST_EFFECTIVE_START": "./resources/last_effective_start.json",
}


def debug_log(func):
    @wraps(func)
    def wrapper_debug(*args, **kwargs):

        if config_local.get("APP_DEBUG"):
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            logging.info(f"Calling {func.__name__}({signature})")

        value = func(*args, **kwargs)

        if config_local.get("APP_DEBUG"):
            logging.info(f"{func.__name__!r} returned {value!r}")

        return value

    return wrapper_debug


class WorkFile:
    """
    # {"обрабатываем":"", "имя файла":"", "время прошлой обработки":"", "результат прошлой обработки":""}
    """
    _file_name = config_local.get("APP_FILE_LAST_EFFECTIVE_START")

    def __init__(self):
        if os.path.exists(self._file_name):

            self.PROCESSING: bool = True
            self.FILE_NAME: str = "nginx-access-ui.log-20170630.gz"
            self.LAST_PROCESSING_DATETIME: str = "2023.12.2012:48:16"
            self.LAST_PROCESSING_RESULT: str = "OK"
            self.LAST_PROCESSING_QUALITY: float = 1.0
        else:
            self.PROCESSING: bool = True
            self.FILE_NAME: str = "nginx-access-ui.log-20170630.gz"
            self.LAST_PROCESSING_DATETIME: str = "2023.12.2012:48:16"
            self.LAST_PROCESSING_RESULT: str = "OK"
            self.LAST_PROCESSING_QUALITY: float = 1.0

    def __str__(self, ):
        return json.dumps(self, default=lambda _: _.__dict__)

    def __repr__(self, ):
        return self.__str__()

    def find(self, logs_path: str):
        """
        # проверить существование пути расположения логов
        # найти самый новый файл
        # проверить, что он не обрабатывался, если уже обрабатывался, то вернуть результат (успех-падение, % охвата)
        # return work_file
        """
        return

    def save(self, ):
        json_object = json.dumps(self, default=lambda o: o.__dict__)
        with open(self._file_name, 'w') as f:
            f.write(json_object)
        return


@debug_log
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


def log_init() -> None:
    """
    Инициализация logging - для DEBUG и NORMAL режимов работы
    :return: None
    """
    # NORMAL mode
    if not config_local.get("APP_DEBUG"):
        loc_file_path = config.get('APP_LOG_FILE_PATH')
        loc_str = '[%(asctime)s] %(levelname).1s %(message)s'
        logging.basicConfig(
            filename=loc_file_path,
            level=logging.INFO,
            format=loc_str,
            datefmt='%Y.%m.%d%H:%M:%S'
        )

    # DEBUG mode
    else:
        loc_file_path = config_local.get('APP_DEBUG_LOG_FILE_PATH')
        loc_dir_path = os.path.dirname(loc_file_path)
        if not os.path.isdir(loc_dir_path):
            os.makedirs(loc_dir_path)

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
    result = {**config}
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='UTF-8') as loc_file:
            config_extra = json.load(loc_file)
        result = {**config, **config_extra}
    else:
        if config_local.get("APP_DEBUG"):
            logging.warning("config file not exist")

    loc_file_name = config_local.get("APP_FILE_LAST_EFFECTIVE_START")
    with open(loc_file_name, 'r', encoding='UTF-8') as loc_file:
        WorkFile = json.load(loc_file)

    if config_local.get("APP_DEBUG"):
        logging.info(result)

    return result


def get_latest_log(logs_path: str) -> typing.Dict:
    # проверить существование пути расположения логов
    # найти самый новый файл
    # проверить, что он не обрабатывался, если уже обрабатывался, то вернуть результат (успех-падение, % охвата)
    # return work_file

    if not os.path.exists(logs_path):
        return

    file_name_template = re.compile(r"""nginx-access-ui\.log-(?P<log_date>\d{8})(\.gz$|$)""", re.IGNORECASE)

    latest_log = None
    for path in os.listdir(logs_path):
        file_log = re.search(file_name_template, path)

        if not file_log or os.path.isdir(path):
            continue

        file_name_data = file_log.groupdict()
        try:
            file_date = datetime.strptime(file_name_data['log_date'], '%Y%m%d').date()
        except ValueError:
            continue

        if not latest_log or latest_log.file_date < file_date:
            latest_log = LogFile(path=os.path.join(logs_path, path), file_date=file_date)

    return latest_log


def main():
    pass


if __name__ == "__main__":
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])

    first_description_print()

    wf = WorkFile()
    print(wf)
    wf.save()

    log_init()
    current_config: typing.Dict = get_config(namespace.config.name)

    main()
