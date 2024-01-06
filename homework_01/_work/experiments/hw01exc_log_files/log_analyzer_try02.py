#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import logging
import os.path
import re
import sys
from argparse import ArgumentParser, FileType
from dataclasses import dataclass, asdict
from datetime import datetime
from functools import wraps

# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


config = {
    "REPORT_SIZE": 1000,
    "LOG_DIR": "./reports",
    "REPORT_DIR": "./log-analyzer",
}


@dataclass(frozen=True)
class ConfigLocal:
    """Сборник локальных параметров. Вместо констант. Изменения запрещены."""

    APP_CONFIG_DEFAULT_PATH: str = "../../../log-analyzer/reports/config.json"  # Стандартный путь расположения config
    APP_FILE_LAST_EFFECTIVE_START: str = "../../../log-analyzer/resources/last_effective_start.json"  # Информация о последнем запуске программы
    APP_LOG_FILE_PATH: str = "./resources/log_analyzer_log.log",  # Файл лога нормального режима

    # шаблон поиска файла
    APP_REGEX_FILE_NAME_TEMPLATE = re.compile(r"""nginx-access-ui\.log-(?P<log_date>\d{8})(\.gz$|$)""", re.IGNORECASE)

    APP_NAME: str = os.path.basename(sys.argv[0]).replace('.py', '')  # Название приложения
    APP_VERSION: str = "0.1.20240104"  # Версия программы

    APP_DEBUG: bool = True  # Режим отладки. True == режим отладки, False == нормальный режим.
    APP_DEBUG_LOG_FILE_PATH: str = "./resources/debug-log/debug_log.log"  # Файл лога режима отладки


def debug_log(func):
    """Декоратор для отладки"""

    @wraps(func)
    def wrapper_debug(*args, **kwargs):
        config_local = ConfigLocal()
        if config_local.APP_DEBUG:
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            logging.info(f"Calling {func.__name__}({signature})")

        value = func(*args, **kwargs)

        if config_local.APP_DEBUG:
            logging.info(f"{func.__name__!r} returned {value!r}")

        return value

    return wrapper_debug


@dataclass
class FileConditions:
    """
     "файл имя":"",
     "файл расширение":"",
     "обработка датавремя":"",
     "обработка результат":"",
     "обработка качество":"",
    """

    file_name: str = ""
    file_type: str = ""
    processing_datetime: str = ""
    processing_result: str = ""
    processing_quality: float = 0.0

    def set(self, settings: dict):
        self.file_name = settings.get("file_name")
        self.file_type = settings.get("file_type")
        self.processing_datetime = settings.get("processing_datetime")
        self.processing_result = settings.get("processing_result")
        self.processing_quality = settings.get("processing_quality")

    def set_from_file(self, filename: str):
        if os.path.exists(filename):
            with open(filename, 'r', encoding='UTF-8') as loc_file:
                self.set(json.load(loc_file))

    def set_debug(self):
        self.set({"file_name": "nginx-access-ui.log-20170630.gz",
                  "file_type": "gz",
                  "processing_datetime": "2023.12.2012:48:16",
                  "processing_result": "OK",
                  "processing_quality": 1.0,
                  })


class WorkFile:
    """
    conditions
     "файл имя":"",
     "файл расширение":"",
     "обработка датавремя":"",
     "обработка результат":"",
     "обработка качество":"",
    """

    def __init__(self, config_local: ConfigLocal, config: dict):
        self.conditions = FileConditions()
        logging.info("Conditions")
        self.conditions.set_from_file(config_local.APP_FILE_LAST_EFFECTIVE_START)
        logging.info(self.conditions)

    def __str__(self, ):
        return json.dumps(self, default=lambda _: _.__dict__)

    def __repr__(self, ):
        return self.__str__()

    def _read_last_result_conditions(self,) -> FileConditions:
        last_file_info = FileConditions()
        if not config_local.APP_DEBUG:
            last_file_info.set_from_file(config_local.APP_FILE_LAST_EFFECTIVE_START)
        else:
            last_file_info.set_debug()

        return last_file_info

    def init_conditions(self, config: dict) -> dict:
        """
        # проверить существование пути расположения логов
        # найти самый новый файл
        # проверить, что он не обрабатывался, если уже обрабатывался, то вернуть результат (успех-падение, % охвата)
        # return work_file
        """
        _target_conditions: FileConditions = self.read_last_result_conditions(self.last_result_conditions_file)
        # найти самый новый файл
        # проверить, что он не обрабатывался, если уже обрабатывался, то вернуть результат (успех-падение, % охвата)
        # return work_file

        latest_log = None
        for path in os.listdir(config.get("LOG_DIR")):
            file_log = re.search(config_local.APP_REGEX_FILE_NAME_TEMPLATE, path)

            if not file_log or os.path.isdir(path):
                continue

            file_name_data = file_log.groupdict()
            try:
                file_date = datetime.strptime(file_name_data['log_date'], '%Y%m%d').date()
            except ValueError:
                continue

            if not latest_log or latest_log.file_date < file_date:
                latest_log = LogFile(path=os.path.join(logs_path, path), file_date=file_date)

        return _target_conditions

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


def create_parser(config_local: ConfigLocal) -> ArgumentParser:
    """
    обработка аргументов и консольного запуска
    :return: ArgumentParser
    """
    loc_prog_name = config_local.APP_NAME
    loc_prog_version = config_local.APP_VERSION
    loc_config_path = config_local.APP_CONFIG_DEFAULT_PATH
    loc_config_debug_mode = config_local.APP_DEBUG

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
def first_description_print(config_local: ConfigLocal) -> None:
    """
    вывод информации при запуске
    """
    loc_prog_name = config_local.APP_NAME
    loc_prog_version = config_local.APP_VERSION
    print(f'{loc_prog_name} v.{loc_prog_version}',
          '- анализатор логов. Создан в рамках ДЗ-01 учебной программы OTUS.')
    return


def log_init(config_local: ConfigLocal) -> None:
    """
    Инициализация logging - для DEBUG и NORMAL режимов работы
    :return: None
    """
    # NORMAL mode
    if not config_local.APP_DEBUG:
        loc_file_path = config_local.APP_LOG_FILE_PATH
        loc_str = '[%(asctime)s] %(levelname).1s %(message)s'
        logging.basicConfig(
            filename=loc_file_path,
            level=logging.INFO,
            format=loc_str,
            datefmt='%Y.%m.%d%H:%M:%S',
            encoding='UTF-8'
        )

    # DEBUG mode
    else:
        loc_file_path = config_local.APP_DEBUG_LOG_FILE_PATH
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
        if config_local.APP_DEBUG:
            logging.warning("config file not exist")

        make_empty_config(config_path)

    with open(config_path, 'r', encoding='UTF-8') as loc_file:
        config_extra = json.load(loc_file)

    # Python 3.9^ -> 'result = config | config_extra' или 'result | = config_extra' - второй у меня не сработал
    if sys.version_info <= (3, 9):
        result = {**config, **config_extra}
    else:
        result = config | config_extra

    if config_local.APP_DEBUG:
        logging.info(result)

    return result


def main():
    pass


if __name__ == "__main__":
    # локальные переменные/ config
    config_local = ConfigLocal()

    # отработка аргументов командной строки
    parser = create_parser(config_local)
    namespace = parser.parse_args(sys.argv[1:])

    first_description_print(config_local)
    log_init(config_local)
    current_config: dict = get_config(namespace.config)

    wf = WorkFile(config_local, current_config)

    print(wf.conditions)

    # wf.save()

    main()
