"""HTTP сервер"""
import logging
import queue
import socket
import threading

from src.config import config
from src.request import RequestHandler


def start_server():
    """Запуск сервера"""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((config.IP, config.PORT))
    server.listen(config.WORKERS)
    logging.info('Listening on %s:%s', config.IP, config.PORT)

    try:
        connection_queue = queue.Queue(config.WORKERS)
        for index in range(config.WORKERS):
            worker = threading.Thread(
                target=RequestHandler,
                args=(index, connection_queue)
            )
            worker.start()

        while True:
            client_sock, address = server.accept()
            logging.info(' ')
            logging.info('Connection %s:%s', address[0], address[1])
            connection_queue.put(client_sock)

    except KeyboardInterrupt:
        logging.info('Server stop')
