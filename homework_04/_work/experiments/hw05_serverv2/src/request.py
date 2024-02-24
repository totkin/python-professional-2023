"""Обработка запроса"""
import logging
import re
from queue import Queue
from socket import socket
from urllib.parse import unquote

from src.config import config
from src.response import ResponseHandler


class RequestHandler:
    """Обработка запроса"""
    method = None
    path = None

    def __init__(self, index, connection_queue: Queue):
        self.__index = index
        self.__queue = connection_queue
        self.__client = None
        self.start()

    def start(self):
        """Получение очереди подключений"""
        logging.info('Thread %s: Request thread started', self.__index)

        while True:
            self.__client: socket = self.__queue.get()
            data: bytes = b''
            while True:
                part = self.__client.recv(config.BUFFER_SIZE)
                data += part
                if not part or b'\r\n\r\n' in part:
                    break
            logging.info('Thread %s: Received %i bytes',
                         self.__index, len(data))

            handler = ResponseHandler()
            if self.parse_request(data.decode('utf-8')):
                response = handler.process(self.method, self.path)
            else:
                response = handler.error('NOT_ALLOWED')
            logging.info('Thread %s: Response (%s)', self.__index,
                         response.splitlines()[0])
            self.__client.sendall(response.encode())
            self.__client.close()
            self.__queue.task_done()

    def parse_request(self, data: str) -> bool:
        """Обработка строки запроса"""
        try:
            regex = re.compile(r"^(" + config.METHODS + r")\s+(\S+)\s+(HTTP)")
            match = regex.findall(data)
            if match:
                path = unquote(match[0][1])
                self.path = path.split('?')[0]
                self.method = match[0][0]
                return True
        except Exception:
            logging.warning('Thread %s: Headers error: %s',
                            self.__index, data.splitlines()[0])
        return False
