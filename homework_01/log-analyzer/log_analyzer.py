#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging

import os.path
import sys
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
    # Стандартный путь расположения config
    "APP_CONFIG_DEFAULT_PATH": "./resources/config.json",
    # Место расположения с информацией о последнем запуске программы
    "APP_FILE_LAST_EFFECTIVE_START": "./resources/last_effective_start.json",
    # Название приложения
    "APP_NAME": os.path.basename(sys.argv[0]).replace('.py', ''),
    # Версия программы
    "APP_VERSION": "0.1.20231229",
    # Режим отладки. True == отладка, False == нормальный режим.
    "APP_DEBUG": True,
    # Файл для лога debug-режима
    "APP_DEBUG_LOG_FILE_PATH": "./resources/debug-log/debug_log.log",
}


def debug_log(func):
    """Декоратор для отладки"""

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

    def __init__(self, last_result_conditions_file: str | None):
        self.last_result_conditions_file = last_result_conditions_file
        self.conditions = self.init_conditions()

    def __str__(self, ):
        return json.dumps(self, default=lambda _: _.__dict__)

    def __repr__(self, ):
        return self.__str__()

    def read_last_result_conditions(self, last_result_file: str | None) -> dict:
        # Файл есть
        if os.path.exists(self.last_result_conditions_file):
            with open(self.last_result_conditions_file, 'r', encoding='UTF-8') as loc_file:
                last_file_info: dict = json.load(loc_file)

        # Файла нет
        else:
            # Нет файла с записью
            # Режим отладки, создаю тестовую версию
            if config_local.get("APP_DEBUG"):
                last_file_info = {"PROCESSING": True,
                                  "FILE_NAME": "nginx-access-ui.log-20170630.gz",
                                  "FILE_TYPE": "gz",
                                  "LAST_PROCESSING_DATETIME": "2023.12.2012:48:16",
                                  "LAST_PROCESSING_RESULT": "OK",
                                  "LAST_PROCESSING_QUALITY": 1.0}

            # Нормальный режим, создаю тестовую версию
            else:
                last_file_info = {"PROCESSING": True,
                                  "FILE_NAME": "",
                                  "FILE_TYPE": "",
                                  "LAST_PROCESSING_DATETIME": "",
                                  "LAST_PROCESSING_RESULT": "",
                                  "LAST_PROCESSING_QUALITY": 1.0}
        return last_file_info

    def init_conditions(self, ) -> dict:
        """
        # проверить существование пути расположения логов
        # найти самый новый файл
        # проверить, что он не обрабатывался, если уже обрабатывался, то вернуть результат (успех-падение, % охвата)
        # return work_file
        """
        target_conditions: dict | None = self.read_last_result_conditions(self.last_result_conditions_file)
        # найти самый новый файл
        # проверить, что он не обрабатывался, если уже обрабатывался, то вернуть результат (успех-падение, % охвата)
        # return work_file

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

        return target_conditions

    def save_result_conditions(self, file_info: dict):
        json_object = json.dumps(file_info, default=lambda o: o.__dict__)
        with open(self.last_result_conditions_file, 'w') as f:
            f.write(json_object)
        return


class Report:

    def __init__(self):
        pass

    def make_report(self):
        pass

    def save_report(self):
        pass


def create_parser() -> ArgumentParser:
    """
    обработка аргументов и консольного запуска
    :return: ArgumentParser
    """
    loc_prog_name = config_local.get("APP_NAME")
    loc_prog_version = config_local.get("APP_VERSION")
    loc_config_path = config_local.get("APP_CONFIG_DEFAULT_PATH")
    loc_config_debug_mode = config_local.get("APP_DEBUG")

    parser: ArgumentParser = ArgumentParser(
        description=f'{loc_prog_name} - анализатор логов. Создан в рамках ДЗ-01 учебной программы OTUS.',
        epilog='(c) T for Otus 2023. Применение ограничено рамками учебной задачи.',
        add_help=False,
    )
    arg_group = parser.add_argument_group(title='Параметры')

    arg_group.add_argument('-c', '--config',
                           # type=FileType(),
                           metavar='',
                           help=f'Файл конфигурации. По-умолчанию это {loc_config_path}',
                           default=loc_config_path,
                           )
    arg_group.add_argument('-v', '--version',
                           action='version',
                           help='Номер версии',
                           version=f'{loc_prog_name} v.{loc_prog_version}')
    arg_group.add_argument('-d', '--debug',
                           type=FileType(),
                           metavar='',
                           help=f'Проверка отключения debug-режима {loc_config_debug_mode}',
                           default=loc_config_debug_mode,
                           )
    arg_group.add_argument('-h', '--help', action='help', help='Справка')

    return parser


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


def make_empty_config(config_path):
    json_object: dict = {}
    with open(config_path, 'w') as f:
        json.dump(json_object, f)


def get_config(config_path) -> dict:
    if not os.path.exists(config_path):
        if config_local.get("APP_DEBUG"):
            logging.warning("config file not exist")

        make_empty_config(config_path)

    with open(config_path, 'r', encoding='UTF-8') as loc_file:
        config_extra = json.load(loc_file)

    # Python 3.9^ -> 'result = config | config_extra' or 'result | = config_extra'
    if sys.version_info <= (3, 9):
        result = {**config, **config_extra}
    else:
        result = config | config_extra

    if config_local.get("APP_DEBUG"):
        logging.info(result)

    return result


def main():
    pass


if __name__ == "__main__":
    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])

    first_description_print()
    log_init()
    current_config: dict = get_config(namespace.config)

    wf = WorkFile(config_local.get("APP_FILE_LAST_EFFECTIVE_START"))

    print(wf.conditions)

    # wf.save()

    main()
