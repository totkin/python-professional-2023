"""Запуск сервиса"""
import logging
from optparse import OptionParser

from src.config import config
from src.server import start_server


def init_logging(filename):
    """Настройка логирования"""
    logging.basicConfig(filename=filename, level=config.LOG_LEVEL,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-w", "--workers", action="store",
                  type=int, default=config.WORKERS)
    op.add_option("-p", "--port", action="store",
                  type=int, default=config.PORT)
    op.add_option("-l", "--log", action="store",
                  type=str, default=config.LOGFILE)
    op.add_option("-r", "--root", action="store",
                  type=str, default=config.DOCUMENT_ROOT)
    (opts, args) = op.parse_args()

    config.WORKERS = opts.workers
    config.PORT = opts.port
    config.DOCUMENT_ROOT = opts.root

    init_logging(opts.log)
    start_server()
