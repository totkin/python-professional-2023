#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import logging
import sys
import uuid
from abc import ABC, abstractmethod, ABCMeta
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


class ValidationError(Exception):
    pass


class ProtoField(ABC):
    required: bool | None = False
    nullable: bool | None = True
    value: object | None

    max_size: int = 256

    error_messages = {}
    error_exception: bool = True  # True - raise Exception, False - add to error_messages

    # None must be in first position
    _empty_values: list = (None, '', [], (), {},)
    _type: object | None = str

    def __set_name__(self, owner, name):
        self._name = name

    def __get__(self, obj, objtype):
        return obj.__dict__.get(self._name)

    def __set__(self, obj, value):
        obj.__dict__[self._name] = value

    @property
    def value_validate(self, ):
        return self.value

    @value_validate.setter
    def value_validate(self, loc_val):
        if self.is_valid:
            self.value = loc_val

    @property
    def type_name(self) -> str:
        if self._type:
            return self._type.__name__.replace("<class ", "").replace(">", "")
        else:
            return ""

    @property
    def is_valid(self) -> bool | None:
        if self.value not in self._empty_values:
            return self._is_valid_mixin
        else:
            return True

    @property
    def _is_valid_mixin(self, ):
        return True

    def __repr__(self):
        a = {_: getattr(self, _) for _ in self.__dir__() if _[0] != '_'}
        a.update({"type": self.type_name})
        return f'<Class {self.__class__.__name__}: {a}>'


class BaseField(ProtoField):

    def __init__(self,
                 required: bool | None = False,
                 nullable: bool | None = True, ) -> None:
        self.required = required
        self.nullable = nullable

    def is_valid(self) -> bool | None:
        value = self.value
        if self.required and value in self._empty_values[0]:
            str_error = f'The field {type(self).__name__} is required'
            if self.error_exception:
                logging.exception(str_error)
                raise ValueError(str_error)
            else:
                self.error_messages.update({'required': str_error})

        if not self.nullable and value in self._empty_values:
            str_error = 'The field cannot be empty'
            if self.error_exception:
                logging.exception(str_error)
                raise ValueError(str_error)
            else:
                self.error_messages.update({'nullable': str_error})

        if self._type:
            if not isinstance(value, self._type):
                str_error = f'The field type must be one of the specified type(s) {self.type_name}'
                # str_error += f'\n{type(value)} not in {target_type}')  # Вариант для print
                if self.error_exception:
                    logging.exception(str_error)
                    raise TypeError(str_error)
                else:
                    self.error_messages.update({'invalid_type': str_error})
                    return False

        return super().is_valid


class CharField(BaseField):
    """строĸа"""
    pass


class ArgumentsField(BaseField):
    """словарь (объеĸт в терминах json)"""
    _type = dict


class EmailField(CharField):
    """строĸа, в ĸоторой есть @"""

    def _is_valid_mixin(self, ):
        value = self.value
        if '@' not in value and value not in self._empty_values:
            str_error = 'The field must contain an email. '
            str_error += 'The string does not contain a character @'
            if self.error_exception:
                logging.exception(str_error)
                raise ValueError(str_error)
            else:
                self.error_messages.update({'invalid_mixin': str_error})
                return False
        return True


class PhoneField(BaseField):
    """строĸа или число, длиной 11, начинается с 7"""
    _type = (int, str)
    _max_size: int = 11

    def _is_valid_mixin(self, ):
        value = self.value
        if value not in self._empty_values:
            max_size = self._max_size
            self.error_messages.update({'invalid_mixin': ()})
            if len(str(value)) != max_size:
                str_error = f'The length of the field must be {max_size} characters. {len(str(value))} != {max_size}'
                # str_error += f'\n{str(value)}\n{" " * max_size-1}^-endpoint' # Вариант для print
                if self.error_exception:
                    logging.exception(str_error)
                    raise ValueError(str_error)
                else:
                    self.error_messages['invalid_mixin'].append(str_error)
                    return False

            if not str(value)[0] == '7':
                str_error = f'The first character must be 7. {str(value)[0]} != 7'
                # str_error += f'\n{str(value)}\n^') # Вариант для print
                if self.error_exception:
                    logging.exception(str_error)
                    raise ValueError(str_error)
                else:
                    self.error_messages['invalid_mixin'].append(str_error)
                    return False

        return True


class DateField(BaseField):
    """дата в формате DD.MM.YYYY"""
    _type = datetime.date

    def _is_valid_mixin(self, ):
        value = self.value
        try:
            datetime.datetime.strptime(value, '%d.%m.%Y')
        except ValueError:
            str_error = 'The field values must be in the DD.MM.YYYY format'
            if self.error_exception:
                logging.exception(str_error)
                raise ValueError(str_error)
            else:
                self.error_messages.update({'invalid_mixin': str_error})
                return False

        return True


class BirthDayField(DateField):
    """
    дата в формате DD.MM.YYYY, с ĸоторой прошло не больше 70 лет
    ДОПОЛНИТЕЛЬНО: сделана проверка на нахождение даты дня рождения в будущем
    """
    _years_limit = 70  # если значение меньше или равно 0 проверка выполняться не будет

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

    def _is_valid_mixin(self, ):
        result = super()._is_valid_mixin

        if result:
            try:
                value = self.value
                if self.age(value) > self._years_limit:
                    str_error = f'More than {self._years_limit} years have passed since {value}'
                    # str_error += f'\n{self.age(value)} > {self._years_limit}') # Вариант для print
                    if self.error_exception:
                        logging.exception(str_error)
                        raise ValueError(str_error)
                    else:
                        self.error_messages.update({'invalid_mixin': str_error})
                        return False

                if self._years_limit > 0 and value > datetime.date.today():
                    str_error = f'The date of the birthday is in the future:{value}'
                    # str_error += f'\n Today in {datetime.date.today()}') # Вариант для print
                    if self.error_exception:
                        logging.exception(str_error)
                        raise ValueError(str_error)
                    else:
                        self.error_messages.update({'invalid_mixin': str_error})
                        return False
                return True
            except ValueError as error:
                if self.error_exception:
                    logging.exception(error)
                    raise ValueError(error)
                else:
                    self.error_messages.update({'invalid_mixin': error})
                    return False
        else:
            return result


class GenderField(BaseField):
    """число 0, 1 или 2"""
    _type = int
    _genders = GENDERS.keys()

    def _is_valid_mixin(self, value):
        if value not in self._genders:
            str_error = f'The field can take the following values: {self._genders}'
            # str_error += f'\n{str(value)} not in {GENDERS.keys()}') # Вариант для print
            if self.error_exception:
                logging.exception(str_error)
                raise ValueError(str_error)
            else:
                self.error_messages.update({'invalid_mixin': str_error})
                return False

        return True


class ClientIDsField(BaseField):
    """массив чисел"""
    _type = list[int]


class MetaRequest(type):
    def __call__(self, *args, **kwargs):
        self.fields = [
            f for f in self.__dict__ if isinstance(self.__dict__.get(f), BaseField)
        ]
        return super().__call__(*args, **kwargs)


class BaseRequest(metaclass=MetaRequest):
    fields = ()

    def __init__(self, **kwargs):
        for field in self.fields:
            setattr(self, field, kwargs.get(field))

    def validate(self):
        errors = {}
        for field in self.fields:
            try:
                value = getattr(self, field)
                descriptor = type(self).__dict__[field]
                if descriptor:
                    descriptor.is_valid
            except ValidationError as e:
                if not errors.get(field):
                    errors[field] = []
                errors[field].append(str(e))

        if errors:
            raise ValidationError(errors)


# OK
class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


# OK
class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def validate(self):
        super().validate()

        def is_valid_pair(a, b):
            return a is not None and b is not None

        any_pair_valid = any(
            (
                is_valid_pair(self.phone, self.email),
                is_valid_pair(self.first_name, self.last_name),
                is_valid_pair(self.gender, self.birthday),
            )
        )
        if any_pair_valid:
            return

        str_error = ("The request must contain one of the specified pairs:" +
                     "(phone/email , first_name/last_name , gender/birthday))")
        raise ValidationError(str_error)


# OK
class MethodRequest(BaseRequest):
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
        str_request = datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
        digest = hashlib.sha512(str_request.encode('utf-8')).hexdigest()
    else:
        str_request = str(request.account) + str(request.login) + str(SALT)
        digest = hashlib.sha512(str_request.encode('utf-8')).hexdigest()
    if digest == request.token:
        return True
    return False


def clients_interests_handler(request, ctx, store):
    clients_interests = ClientsInterestsRequest(**request)
    clients_interests.validate()
    ctx["nclients"] = (
        len(clients_interests.client_ids)
        if clients_interests.client_ids
        else 0
    )
    result = {}
    if clients_interests.client_ids:
        for c_id in clients_interests.client_ids:
            result[c_id] = get_interests(store, None)
    return result, OK


def online_score_handler(request, ctx, store):
    if request.is_admin:
        return {"score": 42}, OK
    arguments = {}
    if request.arguments is not None:
        arguments = request.arguments
    online_score = OnlineScoreRequest(**arguments)
    online_score.validate()
    ctx["has"] = [
        field for field in online_score.fields
        if getattr(online_score, field) is not None
    ]

    score = get_score(
        store,
        online_score.phone,
        online_score.email,
        online_score.birthday,
        online_score.gender,
        online_score.first_name,
        online_score.last_name,
    )

    return {'score': score}, OK


def method_handler(request, ctx, store):
    request_body = request.get("body")

    try:
        method_request = MethodRequest(
            account=request_body.get("account"),
            login=request_body.get("login"),
            method=request_body.get("method"),
            token=request_body.get("token"),
            arguments=request_body.get("arguments"),
        )
        method_request.validate()

        if not check_auth(method_request):
            return None, FORBIDDEN

        # arguments = {}
        # if method_request.arguments is not None:
        #     arguments = method_request.arguments

        if method_request.method == "online_score":
            return online_score_handler(method_request, ctx, store)
        if method_request.method == "clients_interests":
            return clients_interests_handler(method_request.arguments, ctx, store)
    except ValidationError as errors:
        return str(errors), INVALID_REQUEST


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
