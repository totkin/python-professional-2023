import json
import os
import shutil
import unittest
from datetime import datetime

from log_analyzer import LogFile, get_log_file_candidate, main, config, get_config


class TestLogAnalyzer(unittest.TestCase):
    test_path = './test_path'
    report_dir = os.path.join(test_path, 'reports')
    log_dir = os.path.join(test_path, 'log')
    bad_log_dir = os.path.join(test_path, 'bad_log')
    config_dir = os.path.join(test_path, 'config')

    log_dirs = (config_dir, log_dir, bad_log_dir)

    config = {
        'REPORT_SIZE': 10,
        'REPORT_DIR': report_dir,
        'LOG_DIR': log_dir,
        'app_parsing_error_limit_percent': 10,
        'app_template_report_path': os.path.join(test_path, 'report_template.html'),
        'app_config_default_path': os.path.join(config_dir, 'config.json'),
        'app_file_last_start': os.path.join(test_path, "last_effective_start.json"),
    }

    config_name = os.path.join(config_dir, 'config.json')

    # Для тестирования битых логов
    config_add = {
        'REPORT_DIR': bad_log_dir,
        'LOG_DIR': bad_log_dir,
        'app_file_last_start': os.path.join(bad_log_dir, "last_effective_start.json"),
    }

    config_add_name = os.path.join(config_dir, 'config_add.json')

    str_temp = f'nginx-access-ui.log-{datetime.now().strftime("%Y%d%m")}'

    good_file_name = str_temp + '.txt'
    log_files = [
        good_file_name,  # OK
        str_temp + '.bz2',
        str_temp.replace('nginx-access-ui', 'any-data') + '.txt',
    ]

    good_report_file_name = f'report-{datetime.now().strftime("%Y.%d.%m")}.html'

    log_lines = """1.136.218.80 -  - [29/Dec/2023:03:50:29 +0300] "GET 1.0" 200 28 "-" "Mozilla/5.0" "-" "-" "-" 0.005
1.136.218.80 f032b48fb33e1e692  - [29/Dec/2023:03:50:29 +0300] "GET 1.0" 200 28 "-" "Mozilla/5.0" "-" "-" "-" 0.195
1.199.168.100 2a828197ae235b0b3cb  - [29/Dec/2023:03:50:29 +0300] "GET 1.0" 200 28 "-" "Mozilla/5.0" "-" "-" "-" 0.100
1.199.168.111 2a828197ae235b0b3cb  - [29/Dec/2023:03:50:29 +0300] "GET 1.0" 200 28 "-" "Mozilla/5.0" "-" "-" "-" 0.100
"""

    bad_log_lines = """otus.06.01.24 -  - [29/Dec/2023:03:50:29 +0300] "GET 1.0" 200 28 "-" "Mo/5.0" "-" "-" "-" 0.200
1.199.168.100 2a828197ae235b0b3cb  - [29/Dec/2023:03:50:29 +0300] "GET 1.0" 200 28 "-" "Mo/5.0" "-" "-" "-" 0.100
1.199.168.111 2a828197ae235b0b3cb  - [29/Dec/2023:03:50:29 +0300] "GET 1.0" 200 28 "-" "Mo/5.0" "-" "-" "-" 0.100
"""

    @classmethod
    def setUpClass(cls):

        for folder in cls.log_dirs:
            os.makedirs(folder, exist_ok=True)

        with open(os.path.join(cls.test_path, 'report_template.html'), 'w') as f:
            f.write('$target_data')

        for log_file in cls.log_files:
            with open(os.path.join(cls.log_dir, log_file), 'w') as f:
                f.write(cls.log_lines)

        with open(cls.config_name, 'w') as f:
            json.dump(cls.config, f)

        # Битые логи для тестирования
        for log_file in cls.log_files:
            with open(os.path.join(cls.bad_log_dir, log_file), 'w') as f:
                f.write(cls.bad_log_lines)

        #  Коррекция для файла конфигурации
        with open(cls.config_add_name, 'w') as f:
            json.dump(cls.config_add, f)

    def test_get_log_file_candidate(self):
        print('\ntest_get_log_file_candidate run ->')
        current_config = get_config(self.config_name, config)
        log_file: LogFile = get_log_file_candidate(current_config=current_config)
        self.assertEqual(
            log_file.path,
            os.path.join(self.log_dir, self.good_file_name)
        )

    def test_main(self):
        print('\ntest_main ->')
        current_config = get_config(self.config_name, config)
        main(current_config=current_config)

        target_report_path = os.path.join(self.report_dir, self.good_report_file_name)
        self.assertTrue(os.path.exists(target_report_path))

        with open(target_report_path) as f:
            report_value = f.read()

        # проверяекм только первую строку
        target_report_value = '' + \
                              '{"url": "1.136.218.80", "(1) count": 2, "(2) count_perc": "50.00", ' + \
                              '"(3) time_sum": "0.200", "(4) time_perc": "50.00", "(5) time_avg": "0.100", ' + \
                              '"(6) time_max": "0.195", "(7) time_med": "0.100"}'

        self.assertEqual(report_value[1:len(target_report_value) + 1], target_report_value)

    def test_parsing_error_limit_percent(self):
        print('\ntest_parsing_error_limit_percent ->')
        current_config = get_config(self.config_name, config)
        current_config = get_config(self.config_add_name, current_config)

        with self.assertRaises(RuntimeError):
            main(current_config=current_config)

    @classmethod
    def tearDownClass(cls):
        # pass
        shutil.rmtree(cls.test_path, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
