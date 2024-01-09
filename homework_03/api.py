#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import logging
import sys
import uuid
from dataclasses import dataclass

from optparse import OptionParser

if sys.version_info.major >= 3:
    from http.server import HTTPServer, BaseHTTPRequestHandler
else:
    from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

from scoring import get_interests, get_score


@dataclass
class ConfigLocal:
    debug_mode = True  # Режим отладки. True == режим отладки, False == нормальный режим.


SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


class BaseField:
    # None must be in first position
    _empty_values = (None, '', [], (), {},)
    _type: object | None = str

    def __init__(self,
                 required: bool | None = False,
                 nullable: bool | None = True, ) -> None:
        self.required = required
        self.nullable = nullable

    @property
    def value(self, ):
        return self._value

    @value.setter
    def value(self, loc_val):
        self._value = self._is_valid(loc_val)

    def _is_valid(self, value) -> object | None:

        if self.required and value in self._empty_values[0]:
            str_error = f'The field {type(self).__name__} is required'
            logging.exception(str_error)
            raise ValueError()

        if not self.nullable and value in self._empty_values:
            raise ValueError('The field cannot be empty')

        if not isinstance(value, self._type):
            target_type = self._type.__str__().replace("<class ", "").replace(">", "")
            str_error = f'The field type must be one of the specified type(s) {target_type}'
            # str_error += f'\n{type(value)} not in {target_type}')  # Вариант для print
            logging.exception(str_error)
            raise ValueError(str_error)

        if value not in self._empty_values:
            result = self._is_valid_add(value)
        else:
            result = value

        return result

    def _is_valid_add(self, value):
        return value

    def __repr__(self):
        a = {_: getattr(self, _) for _ in self.__dict__ if _[0] != '_'}
        return f'<Class {self.__class__.__name__}: {a}>'


class CharField(BaseField):
    """строĸа"""
    pass


class ArgumentsField(BaseField):
    """словарь (объеĸт в терминах json)"""
    _type = dict


class EmailField(CharField):
    """строĸа, в ĸоторой есть @"""

    def _is_valid_add(self, value):
        if '@' not in value:
            str_error = 'The field must contain an email. '
            str_error += 'The string does not contain a character @'
            logging.exception(str_error)
            raise ValueError(str_error)
        return value


class PhoneField(BaseField):
    """строĸа или число, длиной 11, начинается с 7"""
    _type = (int, str)

    def _is_valid_add(self, value):
        if self.nullable:
            if not str(value)[0] == '7':
                str_error = f'The first character should be 7. {str(value)[0]} != 7'
                # str_error += f'\n{str(value)}\n^') # Вариант для print
                logging.exception(str_error)
                raise ValueError(str_error)
        if len(str(value)) != 11:
            str_error = f'The length of the field must be 11 characters. {len(str(value))} != 11'
            # str_error += f'\n{str(value)}\n{" " * 10}^-endpoint' # Вариант для print
            logging.exception(str_error)
            raise ValueError(str_error)

        return value


class DateField(BaseField):
    """дата в формате DD.MM.YYYY"""
    _type = datetime.date

    def _is_valid_add(self, value):
        try:
            datetime.datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            str_error = 'The field values must be in the DD.MM.YYYY format'
            logging.exception(str_error)
            raise ValueError(str_error)

        return value


class BirthDayField(DateField):
    """
    дата в формате DD.MM.YYYY, с ĸоторой прошло не больше 70 лет
    ДОПОЛНИТЕЛЬНО: сделана проверка на нахождение даты дня рождения в будущем
    """
    _years_limit = 70

    @staticmethod
    def age(check_date: datetime.date, ) -> int:
        today = datetime.date.today()
        if today < check_date:
            return 0
        dob: datetime.date = check_date
        years = today.year - dob.year
        if today.month < dob.month or (today.month == dob.month and today.day < dob.day):
            years -= 1
        return years

    def _is_valid_add(self, value: datetime.date, ):

        super()._is_valid_add(value)

        if self.age(value) > self._years_limit:
            str_error = f'More than {self._years_limit} years have passed since {value}'
            # str_error += f'\n{self.age(value)} > {self._years_limit}') # Вариант для print
            logging.exception(str_error)
            raise ValueError(str_error)
        if value > datetime.date.today():
            str_error = f'The date of the birthday is in the future:{value}'
            # str_error += f'\n Today in {datetime.date.today()}') # Вариант для print
            logging.exception(str_error)
            raise ValueError(str_error)

        return value


class GenderField(BaseField):
    """число 0, 1 или 2"""
    _type = int

    def _is_valid_add(self, value):
        if value not in GENDERS.keys():
            str_error = f'The field can take the following values: {GENDERS.keys()}'
            # str_error += f'\n{str(value)} not in {GENDERS.keys()}') # Вариант для print
            logging.exception(str_error)
            raise ValueError(str_error)

        return value


class ClientIDsField(BaseField):
    """массив чисел"""
    _type = list[int]


# OK
class ClientsInterestsRequest(object):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


# OK - ???
class OnlineScoreRequest(object):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)


# OK
class MethodRequest(object):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


# OK
def check_auth(request):
    if request.is_admin:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def clients_interests_handler(request, ctx, store):
    try:
        r = ClientsInterestsRequest(**request.arguments)
        r.validate()
    except ValueError as err:
        return {
            'code': INVALID_REQUEST,
            'error': str(err)
        }, INVALID_REQUEST

    clients_interests = {}
    for client_id in r.client_ids:
        clients_interests[f'client_id{client_id}'] = get_interests(
            'nowhere_store', client_id)
    return clients_interests, OK


def online_score_handler(request, ctx, store):
    if request.is_admin:
        score = 42
        return {'score': score}, OK
    try:
        r = OnlineScoreRequest(**request.arguments)
        r.validate()
    except ValueError as err:
        return {
            'code': INVALID_REQUEST,
            'error': str(err)
        }, INVALID_REQUEST

    if not r.enough_fields:
        return {
            'code': INVALID_REQUEST,
            'error': 'INVALID_REQUEST: not enough fields'
        }, INVALID_REQUEST

    score = get_score(store, r)
    return {'score': score}, OK


def method_handler(request, ctx, store):
    response, code = None, None
    method = {'clients_interests': clients_interests_handler,
              'online_score': online_score_handler}
    try:
        r = MethodRequest(**request.get('body'))
        r.validate()
    except ValueError as err:
        return {
            'code': INVALID_REQUEST,
            'error': str(err)
        }, INVALID_REQUEST

    if not r.method:
        return {
            'code': INVALID_REQUEST,
            'error': 'INVALID_REQUEST'
        }, INVALID_REQUEST

    if not check_auth(r):
        return None, FORBIDDEN

    response, code = method[r.method](r, ctx, store)
    return response, code


# OK
class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {"method": method_handler}
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        data_string: str | None = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                if sys.version_info < (3, 11):
                    try:
                        response, code = self.router[path]({"body": request, "headers": self.headers}, context,
                                                           self.store)
                    except Exception, e:
                        logging.exception("Unexpected error: %s" % e)
                        code = INTERNAL_ERROR
                else:
                    try:
                        response, code = self.router[path]({"body": request, "headers": self.headers}, context,
                                                           self.store)
                    except Exception as e:
                        logging.exception("Unexpected error: %s" % e)
                        code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


# OK
if __name__ == "__main__":

    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()

    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')

    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
