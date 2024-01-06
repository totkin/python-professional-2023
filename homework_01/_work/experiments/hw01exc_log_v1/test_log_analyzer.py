import json
import os
import shutil
import unittest


from log_analyzer import get_latest_log, analyze, LogFile




class TestLogAnalyzer(unittest.TestCase):
    fixture_dir = './test_fixture'
    log_dir = os.path.join(fixture_dir, 'log')
    log_files = [
        'nginx-access-ui.log-20240106',
        'nginx-access-ui.log-20240106.gz',
        'nginx-access-ui.log-20240106.gz2',
    ]

    report_dir = os.path.join(fixture_dir, 'reports')

    config_dir = os.path.join(fixture_dir, 'config')
    config = {
        'REPORT_SIZE': 10,
        'REPORT_DIR': report_dir,
        'LOG_DIR': log_dir,
        'PARSING_ERROR_LIMIT': 20,
        'TEMPLATE_REPORT_PATH': os.path.join(
            fixture_dir, 'report_template.html'
        )
    }

    @classmethod
    def setUpClass(cls):
        os.makedirs(cls.config_dir, exist_ok=True)
        os.makedirs(cls.log_dir, exist_ok=True)

        with open(
                os.path.join(cls.fixture_dir, 'report_template.html'), 'w'
        ) as f:
            f.write('$table_json')

        for log_file in cls.log_files:
            with open(os.path.join(cls.log_dir, log_file), 'w') as f:
                f.write(
                    '1.196.116.32 -  - [29/Jun/2017:03:50:22 +0300] "GET /api/v2/banner/25019354 HTTP/1.1" 200 927 "-" "Lynx/2.8.8dev.9 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/2.10.5" "-" "1498697422-2190034393-4708-9752759" "dc7161be3" 0.390')  # noqa E501

        with open(os.path.join(cls.config_dir, 'config.json'), 'w') as f:
            json.dump(cls.config, f)

    def test_get_latest_log(self):
        latest_log: LogFile = get_latest_log(self.log_dir)
        self.assertEqual(
            latest_log.path,
            os.path.join(self.log_dir, 'nginx-access-ui.log-20210606')
        )

    def test_analyze(self):
        analyze(config=self.config)

        expected_report_path = os.path.join(
            self.report_dir, 'report-2021.06.06.html'
        )
        self.assertTrue(os.path.exists(expected_report_path))

        with open(expected_report_path) as f:
            report_value = f.read()

        expected_report_value = '[{"url": "/api/v2/banner/25019354 ", ' \
                                '"count": 1, "count_perc": "100.000", ' \
                                '"time_sum": "0.390", ' \
                                '"time_perc": "100.000", ' \
                                '"time_avg": "0.390", "time_max": "0.390", ' \
                                '"time_med": "0.390"}]'
        self.assertEqual(report_value, expected_report_value)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.fixture_dir, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
