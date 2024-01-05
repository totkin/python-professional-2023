import gzip
import json
import logging
import operator
import os
import re
import shutil
import tempfile
import typing
from argparse import ArgumentParser
from collections import namedtuple
from datetime import datetime
from decimal import Decimal
from statistics import mean, median
from string import Template

config_default = {
    'REPORT_SIZE': 1000,
    'reports': './reports',
    'log-analyzer': './log-analyzer',
    'PARSING_ERROR_LIMIT': 20,
    'TEMPLATE_REPORT_PATH': './report_template.html',
    'LOG_FILE_APP_PATH': './log_file.log',
}

LogFile = namedtuple('LogFile', ['path', 'file_date'])


def get_latest_log(logs_path: str) -> typing.Union[LogFile, None]:
    if not os.path.exists(logs_path):
        return

    file_name_template = re.compile(r"""nginx-access-ui\.log-(?P<log_date>\d{8})(\.gz$|$)""", re.IGNORECASE)
    logging.info(file_name_template)
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


def get_log_lines(log_path: str):
    opener = gzip.open if log_path.endswith('.gz') else open
    log_file = opener(log_path, "rt")
    for line in log_file:
        yield line
    log_file.close()


def parse_log(lines, error_limit: int) -> typing.Union[typing.Dict, None]:
    line_format = re.compile(
        r"""- \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"[A-Z]+ )(?P<url>.+)(http\/\d+\.\d+")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["]) (?P<request_time>\d+\.\d+)""",
        # noqa E501
        re.IGNORECASE
    )

    count_lines: int = 0
    count_error: int = 0

    result = {}
    for line in lines:
        count_lines += 1
        line_data = re.search(line_format, line)

        if not line_data:
            count_error += 1
            continue

        datadict = line_data.groupdict()
        url = datadict["url"]
        request_time = Decimal(datadict["request_time"])

        if url in result:
            result[url].append(request_time)
        else:
            result[url] = [request_time]

    check_parsing_result = (count_error / count_lines) * 100 < error_limit
    if check_parsing_result:
        return result
    else:
        raise RuntimeError(f'The threshold value for the number {error_limit} of parsing errors has been exceeded')


def calc_report_data(data: typing.Dict) -> typing.List:
    count_all: int = len(data)

    resp_time_sum = Decimal(0)
    for i in data.values():
        resp_time_sum += sum(i)

    result = []
    for k, v in data.items():
        count_url = len(v)
        resp_time_sum_url = sum(v)
        result.append(
            {
                'url': k,
                'count': count_url,
                'count_perc': Decimal(
                    count_url / count_all * 100
                ).quantize(Decimal('1.111')),
                'time_sum': resp_time_sum_url,
                'time_perc': Decimal(
                    resp_time_sum_url / resp_time_sum * 100
                ).quantize(Decimal('1.111')),
                'time_avg': Decimal(mean(v)).quantize(Decimal('1.111')),
                'time_max': max(v),
                'time_med': median(v)
            }
        )

    result.sort(key=operator.itemgetter('time_sum'), reverse=True)
    return result


def rendering_report(data: typing.List, template_path: str, report_path: str, size: int) -> None:
    with open(template_path, 'r') as t:
        template = Template(t.read())

    report = template.safe_substitute(table_json=json.dumps(data[:size], default=str))

    temp_report_path = tempfile.mkstemp()[1]
    with open(temp_report_path, 'w') as r:
        r.write(report)

    report_dir = os.path.splitext(report_path)[0]
    os.makedirs(report_dir, exist_ok=True)

    shutil.move(temp_report_path, report_path)


def get_config(path) -> typing.Dict:
    with open(path, 'r') as f:
        config_from_file = json.load(f)

    result = {**config_default, **config_from_file}
    return result


def get_arg_parser() -> ArgumentParser:
    parser = ArgumentParser(description='Generating a report with analysis of nginx logs')

    parser.add_argument(
        '--config',
        type=str,
        default='./resources/config.json',
        help='configuration file path  (./resources/config.json)'
    )
    return parser


def analyze(config: typing.Dict) -> None:
    log_file: LogFile = get_latest_log(logs_path=config['log-analyzer'])

    if log_file is None:
        return

    report_path: str = os.path.join(config['reports'],
                                    'report-' + log_file.file_date.strftime('%Y.%m.%d') + '.html')

    if os.path.exists(report_path):
        return

    log_lines = get_log_lines(log_file.path)
    raw_data = parse_log(lines=log_lines, error_limit=config['PARSING_ERROR_LIMIT'])

    if not raw_data:
        return

    report_data: typing.List = calc_report_data(data=raw_data)

    rendering_report(data=report_data, template_path=config['TEMPLATE_REPORT_PATH'],
                     report_path=report_path, size=config['REPORT_SIZE'])


if __name__ == '__main__':

    arg_parser: ArgumentParser = get_arg_parser()
    args = arg_parser.parse_args()

    current_config: typing.Dict = get_config(args.config)

    logging.basicConfig(
        filename=current_config.get('LOG_FILE_APP_PATH'), level=logging.INFO,
        format='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S',
        encoding='UTF-8'
    )

    try:
        analyze(config=current_config)
    except Exception:
        logging.exception('Unexpected error')
