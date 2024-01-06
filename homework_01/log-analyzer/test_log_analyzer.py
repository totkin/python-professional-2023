import json
import os
import unittest
from datetime import datetime

from log_analyzer import LogFile, get_log_file_candidate, main, config, get_config


class TestLogAnalyzer(unittest.TestCase):
    test_path = './test_path'
    report_dir = os.path.join(test_path, 'reports')
    log_dir = os.path.join(test_path, 'log')
    config_dir = os.path.join(test_path, 'config')

    log_dirs = (config_dir, log_dir)

    config = {
        'REPORT_SIZE': 10,
        'REPORT_DIR': report_dir,
        'LOG_DIR': log_dir,
        'app_parsing_error_limit_percent': 10,
        'app_template_report_path': os.path.join(test_path, 'report_template.html'),
        'app_config_default_path': os.path.join(config_dir, 'config.json'),
        'app_file_last_start': os.path.join(test_path, "last_effective_start.json"),
    }
    good_config_name = os.path.join(config_dir, 'config.json')

    str_temp = f'nginx-access-ui.log-{datetime.now().strftime("%Y%d%m")}'

    good_file_name = str_temp + '.txt'
    log_files = [
        good_file_name,  # OK
        str_temp + '.gza',
        str_temp.replace('nginx-access-ui', 'any-data') + '.txt',
    ]

    good_report_file_name = f'report-{datetime.now().strftime("%Y.%d.%m")}.html'

    log_lines = """1.136.218.80 -  - [29/Dec/2023:03:50:29 +0300] "GET /export/appinstall_raw/2017-06-29/ HTTP/1.0" 200 28358 "-" "Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.0.12) Gecko/2009070611 Firefox/3.0.12 (.NET CLR 3.5.30729)" "-" "-" "-" 0.005
1.136.218.80 f032b48fb33e1e692  - [29/Dec/2023:03:50:39 +0300] "GET /api/1/campaigns/?id=4167251 HTTP/1.1" 200 615 "-" "-" "-" "1498697439-4102637017-4709-9929000" "-" 0.195
1.199.168.100 2a828197ae235b0b3cb  - [29/Dec/2023:03:50:56 +0300] "GET /api/1/banners/?campaign=7747171 HTTP/1.1" 200 1600 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697456-2760328665-4709-9929279" "-" 0.100
1.199.168.111 2a828197ae235b0b3cb  - [29/Dec/2023:03:50:56 +0300] "GET /api/1/banners/?campaign=7747171 HTTP/1.1" 200 1600 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697456-2760328665-4709-9929279" "-" 0.100
"""
    bad_log_lines = """otus.136.218.80 -  - [29/Dec/2023:03:50:29 +0300] "GET /export/appinstall_raw/2017-06-29/ HTTP/1.0" 200 28358 "-" "Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.0.12) Gecko/2009070611 Firefox/3.0.12 (.NET CLR 3.5.30729)" "-" "-" "-" 0.003
1.mustafa.76.128 - - -  - [29/Dec/2023:03:50:39 +0300] "GET /api/1/campaigns/?id=4167251 HTTP/1.1" 200 615 "-" "-" "-" "1498697439-4102637017-4709-9929000" "-" 0.141
1.sandal.168.112 2a828197ae235b0b3cb  - [ZZZZZZ] "GET /api/1/banners/?campaign=7747171 HTTP/1.1" 200 1600 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697456-2760328665-4709-9929279" "-" 0.170
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

        with open(os.path.join(cls.config_dir, 'config.json'), 'w') as f:
            json.dump(cls.config, f)

    def test_get_log_file_candidate(self):
        current_config = get_config(self.good_config_name, config)
        log_file: LogFile = get_log_file_candidate(current_config=current_config)
        self.assertEqual(
            log_file.path,
            os.path.join(self.log_dir, self.good_file_name)
        )

    def test_main(self):
        current_config = get_config(self.good_config_name, config)
        main(current_config=current_config)

        target_report_path = os.path.join(self.report_dir, self.good_report_file_name)
        self.assertTrue(os.path.exists(target_report_path))

        with open(target_report_path) as f:
            report_value = f.read()

        target_report_value = '' + \
                              '{"url": "1.136.218.80", "(1) count": 2, "(2) count_perc": "50.00", ' + \
                              '"(3) time_sum": "0.200", "(4) time_perc": "50.00", "(5) time_avg": "0.100", ' + \
                              '"(6) time_max": "0.195", "(7) time_med": "0.100"}'

        self.assertEqual(report_value[1:len(target_report_value) + 1], target_report_value)

    def test_parsing_error_limit_percent(self):
        current_config = get_config(self.good_config_name, config)
        main(current_config=current_config)

        target_report_path = os.path.join(self.report_dir, self.good_report_file_name)
        self.assertTrue(os.path.exists(target_report_path))

        with open(target_report_path) as f:
            report_value = f.read()

        target_report_value = '' + \
                              '{"url": "1.136.218.80", "(1) count": 2, "(2) count_perc": "50.00", ' + \
                              '"(3) time_sum": "0.200", "(4) time_perc": "50.00", "(5) time_avg": "0.100", ' + \
                              '"(6) time_max": "0.195", "(7) time_med": "0.100"}'

        self.assertEqual(report_value[1:len(target_report_value) + 1], target_report_value)

    @classmethod
    def tearDownClass(cls):
        pass
        # shutil.rmtree(cls.test_path, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
