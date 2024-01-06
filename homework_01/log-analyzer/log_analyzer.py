import gzip
import json
import logging
import os
import re
import sys
from argparse import ArgumentParser
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal
from operator import itemgetter
from statistics import mean, median
from string import Template

config = {
    'REPORT_SIZE': 1000,
    'REPORT_DIR': './reports',
    'LOG_DIR': './log-analyzer',
    'app_config_default_path': './resources/config.json',  # Стандартный путь расположения config

    'APP_NAME': os.path.basename(sys.argv[0]).replace('.py', ''),
    'APP_VERSION': '0.1.20240105',

    'app_debug': False,  # Режим отладки. True == режим отладки, False == нормальный режим.
    'app_debug_log_file_path': "./resources/debug_log_file.log",  # Файл лога режима отладки

    'app_parsing_error_limit_percent': 20,
    'app_template_report_path': './resources/report_template.html',
    'app_log_file_app_path': './resources/log_file.log',
    # Паттерн для поиска файлов логов
    'app_file_regex_template': re.compile(
        r'nginx-access-ui\.log-(?P<filename_date>\d{8})\.(?P<file_extension>[0-9a-z]+$)', re.IGNORECASE),
    # Допустимые расширения файла логов : функция для работы с файлом
    'app_correct_log_files_extensions': {'gz': gzip.open,
                                         'txt': open,
                                         },
    # Информация о последнем запуске программы
    'app_file_last_start': "./resources/last_effective_start.json",
    # Паттерн для чтения строк
    # log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
    #                     '$status $body_bytes_sent "$http_referer" '
    #                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
    #                     '$request_time';
    'app_line_regex_template':
        re.compile(
            ''
            + r'(?P<remote_addr>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) '
            + r'(?P<remote_user>.+?)  '
            + r'(?P<http_x_real_ip>[0-9a-z]+|-) '
            + r'\[(?P<time_local>\d{2}\/[A-Za-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] '
            + r'\"(?P<request>.+?)\" '
            + r'(?P<status>\d{1,3}) '
            + r'(?P<body_bytes_sent>\d+) '
            + r'\"(?P<http_referer>.+?)\" '
            + r'\"(?P<http_user_agent>.+?)\" '
            + r'\"(?P<http_x_forwarded_for>.+?)\" '
            + r'\"(?P<http_X_REQUEST_ID>.+?)\" '
            + r'\"(?P<http_X_RB_USER>.+?)\" '
            + r'(?P<request_time>\d+\.\d+)',
            re.IGNORECASE),
    'app_encoding': 'UTF-8',
}


@dataclass
class LogFile:
    path: str = ""
    extension: str = ""
    date: date = datetime.strptime('19700101', "%Y%d%m").date()
    status: bool = False,
    percent_error: Decimal('1.000') = 0.0

    def to_json(self, ):
        """ Простая заплатка из-за использования datetime.date и Decimal"""

        temp_str = f'"path": "{self.path}", "extension": "{self.extension}", "date": "{self.date}", '
        temp_str += f'"status": {json.dumps(self.status)}, "percent_error": {json.dumps(self.percent_error)}'
        temp_str = '{' + temp_str + '}'

        return temp_str


def create_parser(current_config: dict) -> ArgumentParser:
    """
    обработка аргументов и консольного запуска
    :return: ArgumentParser
    """
    loc_prog_name = current_config.get('APP_NAME')
    loc_prog_version = current_config.get('APP_VERSION')
    loc_config_path = current_config.get('app_config_default_path')
    loc_config_debug_mode = current_config.get('app_debug')

    parser: ArgumentParser = ArgumentParser(
        description=f'{loc_prog_name} - анализатор логов. Создан в рамках ДЗ-01 учебной программы OTUS.',
        epilog='(c) T for Otus 2024. Применение ограничено рамками учебной задачи.',
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
    arg_group.add_argument('-h', '--help', action='help', help='Справка')

    return parser


def first_description_print(current_config: dict) -> None:
    """
    вывод информации при запуске
    """
    loc_prog_name = current_config.get('APP_NAME')
    loc_prog_version = current_config.get('APP_VERSION')

    print(f'{loc_prog_name} v.{loc_prog_version}',
          '- анализатор логов. Создан в рамках ДЗ-01 учебной программы OTUS.')
    return


def log_init(current_config: dict) -> None:
    """
    Инициализация logging - для DEBUG и NORMAL режимов работы
    :return: None
    """
    app_debug = current_config.get('app_debug')
    encoding = current_config.get('app_encoding')

    # NORMAL mode

    if not app_debug:
        loc_file_path = current_config.get('app_log_file_app_path')
        loc_str = '[%(asctime)s] %(levelname).1s %(message)s'
        logging.basicConfig(
            filename=loc_file_path,
            level=logging.INFO,
            format=loc_str,
            datefmt='%Y.%m.%d %H:%M:%S',
            encoding=encoding,
        )

    # DEBUG mode
    else:
        loc_file_path = current_config.get('app_debug_log_file_path')
        loc_dir_path = os.path.dirname(loc_file_path)
        os.makedirs(loc_dir_path, exist_ok=True)

        loc_str = "%(asctime)s;%(levelname)s;%(funcName)s;%(lineno)d;%(message)s"
        logging.basicConfig(
            filename=loc_file_path,
            level=logging.INFO,
            format=loc_str,
            datefmt='%Y.%m.%d %H:%M:%S',
            filemode="w",
            encoding=encoding,
        )
        logging.info("Log start")

    return


def get_config(config_path: str, local_config: dict) -> dict:
    app_debug = local_config.get('app_debug')
    encoding = local_config.get('app_encoding')

    if not os.path.exists(config_path):
        if app_debug:
            logging.warning("Не существует файла конфигурации. Создаю пустой.")
        with open(config_path, 'w') as f:
            json.dump({}, f)

    with open(config_path, 'r', encoding=encoding) as loc_file:
        config_extra = json.load(loc_file)

    # Python 3.9^ -> 'result = config | config_extra' или 'result | = config_extra' - второй у меня не сработал
    if sys.version_info <= (3, 9):
        result = {**local_config, **config_extra}
    else:
        result = local_config | config_extra

    if app_debug:
        logging.info(result)

    return result


def duple_info(str_info: str):
    logging.info(str_info)
    print(str_info)


def get_log_file_candidate(current_config: dict) -> LogFile:
    result_file = LogFile()
    file_regex_template = current_config.get('app_file_regex_template')
    logs_dir = current_config.get('LOG_DIR')
    correct_log_files_extensions = list(current_config.get('app_correct_log_files_extensions').keys())

    if os.path.exists(logs_dir):
        for file in os.listdir(logs_dir):
            if not os.path.isdir(file):
                file_log = re.search(file_regex_template, file)
                if file_log:
                    file_dict = file_log.groupdict()
                    try:
                        file_date = datetime.strptime(file_dict['filename_date'], '%Y%m%d').date()
                        file_extension = file_dict['file_extension']
                    except ValueError:
                        logging.exception(ValueError)
                        continue

                    if file_date > result_file.date and file_extension in correct_log_files_extensions:
                        try:
                            result_file = LogFile(path=os.path.join(logs_dir, file),
                                                  extension=file_dict['file_extension'],
                                                  date=file_date,
                                                  status=True)
                        except Exception:
                            logging.exception(Exception)
    else:
        str_info = f'Папки с логами {logs_dir} не существует.'
        logging.info(str_info)
        print(str_info)
        return result_file

    if result_file.path == '':

        str_info = f"Нет файлов логов в папке {logs_dir} с допустимыми расширениями {correct_log_files_extensions}"
        logging.info(str_info)
        print(str_info)
    else:
        str_info = f"Найден файл-кандидат на обработку {result_file.path}"
        logging.info(str_info)
        print(str_info)
        result_file = check_log_file_candidate(current_config, result_file)

    return result_file


def check_log_file_candidate(current_config: dict, result_file: LogFile) -> LogFile:
    filename = current_config.get('app_file_last_start')
    encoding = current_config.get('app_encoding')
    conditions: dict = {}
    if os.path.exists(filename):
        with open(filename, 'r', encoding=encoding) as loc_file:
            conditions = json.load(loc_file)
    if (conditions != {}
            and conditions.get("path").__repr__() == "'" + result_file.path.__str__() + "'"
            and conditions.get('status')):
        if conditions.get('status'):
            str_info = f'Файл уже был успешно обработан ранее: {conditions}'
            logging.info(str_info)
            print(str_info)

            result_file = LogFile()
    return result_file


def get_report_name(current_config: dict, log_file: LogFile) -> str:
    report_dir = current_config.get('REPORT_DIR')
    report_name = f"report-{log_file.date.strftime('%Y.%m.%d')}.html"
    report_path: str = os.path.join(report_dir, report_name)
    if os.path.exists(report_path):
        str_info = f'Файл с отчетом {report_path} уже существует и будет перезаписан.'
        logging.info(str_info)
        print(str_info)
    return report_path


def read_file_line_by_line(log_file: LogFile, current_config: dict, ):
    correct_log_files_extensions: dict = current_config.get('app_correct_log_files_extensions')
    open_with = correct_log_files_extensions.get(log_file.extension)
    _encoding = current_config.get('app_encoding')

    file = open_with(log_file.path, mode='rt', encoding=_encoding)
    for _ in file:
        yield _
    file.close()


def parse_file(rows, log_file: LogFile, current_config: dict, ) -> dict | None:
    """Чтение данных из файла с логами"""
    error_limit_percent = current_config.get('app_parsing_error_limit_percent')
    line_format = current_config.get('app_line_regex_template')

    count_lines: int = 0
    count_error: int = 0

    result = {}

    for row in rows:
        count_lines += 1
        line_data = re.search(line_format, row)

        if not line_data:
            count_error += 1
        else:
            datadict = line_data.groupdict()

            remote_addr = datadict['remote_addr']
            request_time = datadict['request_time']

            if remote_addr not in result:
                result[remote_addr] = []
            result[remote_addr].append(Decimal(request_time))

    check_parsing_result = (count_error / count_lines) * 100
    log_file.percent_error = check_parsing_result
    check_parsing_result = check_parsing_result < error_limit_percent
    if check_parsing_result:
        str_info = f'Обработано строк: {count_lines}. Ошибок: {count_error}'
        logging.info(str_info)
        print(str_info)
        log_file.status = True
        return result
    else:
        str_info = f'Обработано строк:{count_lines}. Ошибок: {count_error}'
        logging.info(str_info)
        print(str_info)
        log_file.status = False
        save_file_last_start(log_file, current_config)
        raise RuntimeError(f'Кол-во ошибок при парсинге лога превысило установленный порог в {error_limit_percent} %')


def save_file_last_start(log_file: LogFile, current_config: dict, ):
    """ Сохранить результаты обработки """

    encoding = current_config.get('app_encoding')
    file_last_start = current_config.get('app_file_last_start')

    json_object = log_file.to_json()
    with open(file_last_start, 'w', encoding=encoding) as f:
        f.write(json_object)
    return


def get_report_data(data_dict: dict, ) -> list:
    """ На основе считанных данных, готовится выходной массив информации

        # Report data
        # count      - сĸольĸо раз встречается URL, абсолютное значение
        # count_perc - сĸольĸо раз встречается URL, в процентах относительно общего числа запросов
        # time_sum   - суммарный $request_time для данного URL'а, абсолютное значение
        # time_perc  - суммарный $request_time для данного URL'а, в процентах относительно
                       общего $request_time всех запросов
        # time_avg   - средний $request_time для данного URL'а
        # time_max   - маĸсимальный $request_time для данного URL'а
        # time_med   - медиана $request_time для данного URL'а

        Использую нумерацию столбцов для сортировки (и КРАСОТЫ!)
    """
    resp_time_sum = 0
    count_all: int = 0
    for i in data_dict.values():
        resp_time_sum += sum(i)
        count_all += len(i)

    result = []
    for u, v in data_dict.items():
        count_url = len(v)
        count_perc = count_url / count_all * 100
        resp_time_sum_url = sum(v)
        time_perc = resp_time_sum_url / resp_time_sum * 100

        result.append(
            {
                'url': u,
                '(1) count': count_url,
                '(2) count_perc': Decimal(count_perc).quantize(Decimal('1.00')),
                '(3) time_sum': Decimal(resp_time_sum_url).quantize(Decimal('1.000')),
                '(4) time_perc': Decimal(time_perc).quantize(Decimal('1.00')),
                '(5) time_avg': Decimal(mean(v)).quantize(Decimal('1.000')),
                '(6) time_max': Decimal(max(v)).quantize(Decimal('1.000')),
                '(7) time_med': Decimal(median(v)).quantize(Decimal('1.000')),
            }
        )

    str_info = f'Общее число url в логе: {len(result)}'
    logging.info(str_info)
    print(str_info)
    result.sort(key=itemgetter('(3) time_sum'), reverse=True)
    return result


def make_report(data: list, report_path: str, current_config: dict, ) -> None:
    report_size = current_config.get('REPORT_SIZE')
    report_dir = current_config.get('REPORT_DIR')
    template_path = current_config.get('app_template_report_path')
    encoding = current_config.get('app_encoding')

    with open(template_path, 'r', encoding=encoding) as t:
        template = Template(t.read())

    report = template.safe_substitute(target_data=json.dumps(data[:report_size], default=str, sort_keys=False))

    os.makedirs(report_dir, exist_ok=True)
    with open(report_path, 'w', encoding=encoding) as r:
        r.write(report)

    str_info = f'В отчет размещено {report_size} строк.'
    logging.info(str_info)
    print(str_info)


def main(current_config: dict):
    log_file: LogFile = get_log_file_candidate(current_config=current_config)

    if log_file.path != '':
        line_by_line = read_file_line_by_line(log_file, current_config)
        raw_data: dict | None = parse_file(line_by_line, log_file, current_config)
        rep_data: list = get_report_data(raw_data)

        rep_file: str = get_report_name(current_config, log_file)
        make_report(data=rep_data, report_path=rep_file, current_config=current_config)

        save_file_last_start(log_file, current_config)
    else:
        str_info = 'Не найдено файлов для обработки.'
        logging.info(str_info)
        print(str_info)


if __name__ == '__main__':

    # отработка аргументов командной строки
    parser = create_parser(config)
    namespace = parser.parse_args(sys.argv[1:])

    first_description_print(config)
    log_init(config)
    current_config: dict = get_config(namespace.config, config)

    try:
        start_time = datetime.now()
        main(config)
        str_info = f'Длительность операции: {datetime.now() - start_time}'
        logging.info(str_info)
        print(str_info)

    except Exception:
        logging.exception('Unexpected error')
