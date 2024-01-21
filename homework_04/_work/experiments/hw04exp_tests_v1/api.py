#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import logging
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from optparse import OptionParser
from typing import Optional

from scoring import get_interests, get_score
from store import Store

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


ValidationError = ValueError


class BaseField:
    required: bool
    nullable: bool

    def __init__(self, required: bool, nullable: bool):
        if not required and not nullable:
            raise ValueError("Optional field must be nullable")
        self.required = required
        self.nullable = nullable

    def __set_name__(self, owner, name):
        self._name = name
        self._private_name = f"_{self._name}"

    def __get__(self, instance, owner):
        return getattr(instance, self._private_name)

    def _validate(self, field_value):
        if not self.nullable and field_value is None:
            raise ValidationError(
                f'Field "{self._name}" is not nullable but is set to null or not provided in request'
            )
        return field_value

    def __set__(self, instance, value):
        setattr(instance, self._private_name, self._validate(value))


class CharField(BaseField):
    def _validate(self, field_value) -> Optional[str]:
        value = super()._validate(field_value)
        if value is not None and not isinstance(value, str):
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: string is expected but object of type {type(field_value).__name__} received'
            )
        return value


class ArgumentsField(BaseField):
    def _validate(self, field_value) -> dict[str, any]:
        value = super()._validate(field_value)
        if value is None:
            return {}

        if not isinstance(value, dict):
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: JSON object expected but object of type {type(field_value).__name__} received'
            )

        if not all(isinstance(key, str) for key in value):
            raise ValidationError(
                f'JSON object "{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: all keys of method arguments object must be strings'
            )

        return value


class EmailField(CharField):
    def _validate(self, field_value) -> Optional[str]:
        value = super()._validate(field_value)
        if value is None:
            return

        if '@' not in value:
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: e-mail address must contain \'@\' symbol'
            )

        return value


class PhoneField(BaseField):
    PHONE_LENGTH = 11
    PHONE_CODE = '7'

    def _validate(self, field_value) -> Optional[str]:
        value = super()._validate(field_value)
        if value is None:
            return

        if not isinstance(value, (int, str)):
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: phone number must be either string or number '
                f'but object of type {type(field_value).__name__} received'
            )

        value = str(value)

        if len(value) != self.PHONE_LENGTH:
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: phone number must contain {self.PHONE_LENGTH} digits '
                f'but "{json.dumps(field_value)}" contains {len(value)}'
            )

        if self.PHONE_LENGTH > 0 and value[0] != self.PHONE_CODE:
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: phone number must start with code {self.PHONE_CODE}'
            )

        return value


class DateField(CharField):
    def _validate(self, field_value) -> Optional[datetime.datetime]:
        value = super()._validate(field_value)
        if value is None:
            return

        try:
            value = datetime.datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: "{json.dumps(field_value)}" is not a valid date in DD.MM.YYYY format'
            ) from None

        return value


class BirthDayField(DateField):
    MAX_AGE = 70

    def _validate(self, field_value) -> Optional[datetime.datetime]:
        value = super()._validate(field_value)
        if value is None:
            return

        today = datetime.datetime.today()
        age = int(today.year - value.year - ((today.month, today.day) < (value.month, value.day)))
        if age < 0:
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: maximum accepted age is {self.MAX_AGE} year(s) '
                f'but birth date of "{json.dumps(field_value)}" suggests negative age'
            )
        if age > self.MAX_AGE:
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: maximum accepted age is {self.MAX_AGE} year(s) '
                f'but birth date of "{json.dumps(field_value)}" suggests age of {age} year(s)'
            )

        return value


class GenderField(BaseField):
    VALID_GENDERS = [MALE, FEMALE, UNKNOWN]

    def _validate(self, field_value) -> Optional[int]:
        value = super()._validate(field_value)
        if value is None:
            return

        if value not in self.VALID_GENDERS:
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: gender must be one of the following values: ' + ", ".join(map(str, self.VALID_GENDERS))
            )

        return field_value


class ClientIDsField(BaseField):
    def __init__(self, required: bool):
        super().__init__(required, nullable=False)

    def _validate(self, field_value) -> list[int]:
        value = super()._validate(field_value)

        if not isinstance(value, list):
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: client IDs must be a list of integers '
                f'but object of type {type(field_value).__name__} received'
            )
        if len(value) == 0:
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: client IDs list must not be empty'
            )
        if not all(isinstance(client_id, int) for client_id in value):
            raise ValidationError(
                f'"{json.dumps(field_value)}" is not a valid value for field "{self._name}"; '
                f'reason: client IDs must be a list of integers '
                f'but some of list elements are not integers'
            )

        return value


class RequestFieldMetaclass(type):
    def __new__(mcs, name, bases, dct):
        cls = None

        def init(self, request: dict):
            field_names = []
            for field_name, field in dct.items():
                if isinstance(field, BaseField):
                    if field_name not in request and field.required:
                        raise ValidationError(
                            f'Field "{field_name}" is required but not provided in request'
                        )
                    field_value = request.get(field_name)
                    field.__set__(self, field_value)
                    field_names.append(field_name)

            super(cls, self).__init__(request)
            self._field_names.extend(field_names)

            if hasattr(self, '_validate'):
                self._validate()

        cls = super().__new__(mcs, name, bases, {'__init__': init, **dct})  # late binding, oh Jesus
        return cls


class BaseRequest(metaclass=RequestFieldMetaclass):
    def __init__(self, request: dict):
        self._field_names = []


class ClientsInterestsRequest(BaseRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)


class OnlineScoreRequest(BaseRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def _validate(self):
        if (
            (self.first_name is None or self.last_name is None)
            and (self.email is None or self.phone is None)
            and (self.birthday is None or self.gender is None)
        ):
            raise ValidationError("Not enough data provided")


class MethodRequest(BaseRequest):
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN


def check_auth(request: MethodRequest):
    if request.is_admin:
        digest = hashlib.sha512((datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).encode()).hexdigest()
    else:
        digest = hashlib.sha512((request.account + request.login + SALT).encode()).hexdigest()
    if digest == request.token:
        return True
    return False


def online_score_handler(request: dict, is_admin: bool, ctx: dict, store) -> tuple[any, int]:
    online_score_request = OnlineScoreRequest(request)
    if not is_admin:
        response = {
            "score": get_score(
                store=store,
                phone=online_score_request.phone,
                email=online_score_request.email,
                birthday=online_score_request.birthday,
                gender=online_score_request.gender,
                first_name=online_score_request.first_name,
                last_name=online_score_request.last_name
            )
        }
    else:
        response = {"score": 42}
    code = OK

    ctx['has'] = [
        field_name
        for field_name in online_score_request._field_names
        if getattr(online_score_request, field_name) is not None
    ]

    return response, code


def clients_interests_handler(request: dict, ctx: dict, store) -> tuple[any, int]:
    clients_interests_request = ClientsInterestsRequest(request)

    response = {
        client_id: get_interests(store, client_id)
        for client_id in clients_interests_request.client_ids
    }
    code = OK

    ctx['nclients'] = len(response)

    return response, code


def method_handler(request: dict, ctx: dict, store) -> tuple[any, int]:
    try:
        method_request = MethodRequest(request['body'])

        if not check_auth(method_request):
            response = "Invalid authentication token"
            code = FORBIDDEN
            return response, code

        if method_request.method == "online_score":
            response, code = online_score_handler(method_request.arguments, method_request.is_admin, ctx, store)
        elif method_request.method == "clients_interests":
            response, code = clients_interests_handler(method_request.arguments, ctx, store)
        else:
            response = f"Requested method {method_request.method} not found"
            code = NOT_FOUND
    except ValidationError as e:
        response = str(e)
        code = INVALID_REQUEST

    return response, code


class StoringHTTPServer(HTTPServer):
    def __init__(self, *args, storage_address=('localhost', 6379), **kwargs):
        self.store = Store(storage_address[0], storage_address[1])
        super(StoringHTTPServer, self).__init__(*args, **kwargs)

    def server_activate(self):
        self.store.connect()
        super(StoringHTTPServer, self).server_activate()

    def server_close(self):
        super(StoringHTTPServer, self).server_close()
        self.store.disconnect()


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length'])).decode("utf-8")
            request = json.loads(data_string)
        except Exception as e:
            response = f"Error reading or parsing request: {e}"
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers},
                        context,
                        self.server.store
                    )
                except Exception as e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                response = f"Path {self.path} not found"
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
        self.wfile.write(json.dumps(r).encode('utf-8'))
        return


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("--storage-host", action="store", default="localhost")
    op.add_option("--storage-port", action="store", type=int, default=6379)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = StoringHTTPServer(("localhost", opts.port), MainHTTPHandler,
                               storage_address=(opts.storage_host, opts.storage_port))
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
