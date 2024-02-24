"""Обработка ответа"""
import logging
import os
from datetime import datetime

from src.config import config


class ResponseHandler:
    """Обработка ответа"""
    method = None
    path = None
    mime_type = None

    def __init__(self):
        self.__root = os.path.normpath(os.path.join(
            os.path.dirname(__file__), '..', config.DOCUMENT_ROOT))

    def process(self, method, path) -> str:
        """Обработка ответа"""
        self.method = method
        self.path = path
        try:
            path = self.parse_path()
            self.mime_type = self.get_mime_type(path)
            with open(path, 'rb') as file:
                content = file.read()
            return self.generate_response('OK', content)
        except ValueError as error:
            logging.error('Response process error: %s', error)
            return self.error(str(error))

    def error(self, value) -> str:
        """Обработка ошибки"""
        self.mime_type = config.MIME_TYPES.get('html')
        self.method = 'GET'
        description = f'{config.CODE.get(value)} {config.ERRORS.get(value)}'
        content = f'<html><head><title>{description}</title></head>' \
                  f'<body><h1>{description}</h1><hr/>' \
                  f'{config.SERVER_NAME}</body></html>'
        return self.generate_response(value, content.encode())

    def generate_response(self, value: str, content: bytes) -> str:
        """Формирование ответа"""
        lines = [
            f'HTTP/1.1 {config.CODE.get(value)} {config.ERRORS.get(value)}',
            'Cache-Control: no-cache, no-store, max-age=0, must-revalidate',
            f'Date: {datetime.today().strftime("%a, %d %b %Y %H:%M:%S %Z")}',
            f'Server: {config.SERVER_NAME}',
            'Expires: 0',
            'Pragma: no-cache',
            f'Content-Type: {self.mime_type}',
            f'Content-Length: {len(content)}',
            'Connection: close',
        ]
        if self.method == 'GET':
            if 'text' in self.mime_type:
                content = content.decode('utf-8')
            lines.append(f'\r\n{content}')

        lines.append('\r\n')
        return '\r\n'.join(lines)

    @staticmethod
    def get_mime_type(path: str) -> str:
        """Получение типа файла"""
        _, extension = os.path.splitext(path)
        return config.MIME_TYPES.get(extension.replace('.', ''),
                                     'application/octet-stream')

    def parse_path(self) -> str:
        """Проверка пути"""
        path = os.path.normpath(os.path.join(self.__root, self.path[1:]))
        if self.__root not in path:
            raise ValueError('FORBIDDEN')

        not_found_conditions = [
            not os.path.exists(path),
            os.path.isfile(path) and self.path[-1] == '/',
            os.path.isdir(path) and not os.path.exists(f'{path}/index.html'),
        ]
        if any(not_found_conditions):
            raise ValueError('NOT_FOUND')

        return path if os.path.isfile(path) else f'{path}/index.html'
