#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import hashlib
import json
import logging
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from optparse import OptionParser

from scoring import get_interests, get_score

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


class BaseField:
    required: bool
    nullable: bool

    error_messages = {}
    error_exception: bool = True  # True - raise Exception, False - add to error_messages

    # None must be in first position
    _null_values: list = (None, '', [], (), {},)

    def __init__(self,
                 required: bool | None = False,
                 nullable: bool | None = True, ):
        if not required and not nullable:
            str_error = "Optional field must be nullable"
            if self.error_exception:
                logging.exception(str_error)
                raise ValueError(str_error)
        self.required = required
        self.nullable = nullable

    def __set_name__(self, owner, name):
        self._name = name
        self._private_name = f"_{self._name}"

    def __get__(self, instance, owner):
        return getattr(instance, self._private_name)

    def __set__(self, instance, value):
        setattr(instance, self._private_name, self.valid_value(value))

    def valid_value(self, value_candidate):
        if not self.nullable and value_candidate is None:
            str_error = f'Field "{self._name}" is not nullable but is set to null or not provided in request'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'nullable': str_error})

        if self.required and value_candidate is self._null_values[0]:
            str_error = f'Field {type(self).__name__} is required'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'required': str_error})

        return value_candidate


class CharField(BaseField):

    def valid_value(self, value) -> str | None:
        value = super().valid_value(value)
        if value in self._null_values:
            return value

        if value is not None and not isinstance(value, str):
            str_error = f'Validation Error: string is expected but object of type {type(value).__name__} received'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})
        return value


class ArgumentsField(BaseField):

    def valid_value(self, field_value) -> dict[str, any]:
        value = super().valid_value(field_value)

        if value in self._null_values:
            return {}

        if not isinstance(value, dict):
            str_error = f'Validation Error: JSON object expected but object of type {type(value).__name__} received'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})

        if not all(isinstance(key, str) for key in value):
            str_error = 'Validation Error: all keys of method arguments object must be strings'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})

        return value


class EmailField(CharField):

    def valid_value(self, field_value) -> str | None:
        value = super().valid_value(field_value)
        if value in self._null_values:
            return value

        if '@' not in value:
            str_error = 'Validation Error: The string does not contain a character "@"'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})

        return value


class PhoneField(BaseField):
    PHONE_LENGTH = 11
    PHONE_CODE = '7'

    def valid_value(self, field_value) -> str | None:
        value = super().valid_value(field_value)
        if value in self._null_values:
            return value

        if not isinstance(value, (str, int)):
            str_error = 'Validation Error:'
            str_error += f'string or number is expected but object of type {type(value).__name__} received'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})

        value = str(value)

        if len(value) != self.PHONE_LENGTH:
            str_error = 'Validation Error: the length of the field must be {self.PHONE_LENGTH} characters.'
            str_error += f' {len(str(value))} != {self.PHONE_LENGTH}'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})

        if self.PHONE_LENGTH > 0 and value[0] != self.PHONE_CODE:
            str_error = f'Validation Error: The first character must be {str(value)[0]}. {str(value)[0]} != 7'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})

        return value


class DateField(BaseField):

    def valid_value(self, field_value) -> datetime.datetime | None:
        value = super().valid_value(field_value)
        if value in self._null_values:
            return value

        try:
            value = datetime.datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            str_error = 'Validation Error: The field values must be in the DD.MM.YYYY format'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})

        return value


class BirthDayField(DateField):
    MAX_AGE = 70

    def age(self, value):
        value = datetime.datetime.strptime(value, "%d.%m.%Y")
        today = datetime.datetime.today()
        result = int(today.year - value.year - ((today.month, today.day) < (value.month, value.day)))
        return result

    def valid_value(self, field_value) -> datetime.datetime | None:
        value = super().valid_value(field_value)
        if value in self._null_values:
            return value

        age = self.age(field_value)
        if age < 0:
            str_error = f'Validation Error: the date of the birthday is in the future:{field_value}'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})
        if age > self.MAX_AGE:
            str_error = f'Validation Error: maximum accepted age is {self.MAX_AGE} year(s)'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})

        return value


class GenderField(BaseField):
    VALID_GENDERS = GENDERS.keys()

    def valid_value(self, field_value) -> int | None:
        value = super().valid_value(field_value)
        if value in self._null_values:
            return value

        if value not in self.VALID_GENDERS:
            str_error = f'Validation Error: the field can take the following values: {self.VALID_GENDERS}'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})

        return field_value


class ClientIDsField(BaseField):

    def __init__(self, required: bool):
        super().__init__(required, nullable=False)

    def valid_value(self, field_value) -> list[int]:
        value = super().valid_value(field_value)

        if not isinstance(value, list):
            str_error = 'Validation Error: client IDs must be a list of integers'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})
        if len(value) == 0:
            str_error = 'Validation Error: client IDs list must not be empty'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})
        if not all(isinstance(client_id, int) for client_id in value):
            str_error = 'Validation Error: client IDs must be a list of integers'
            if self.error_exception:
                raise ValidationError(str_error)
            else:
                logging.exception(str_error)
                self.error_messages.update({'type': str_error})

        return value


class MetaRequest(type):
    def __new__(mcs, class_name, parents, attributes):
        def init(self, request: dict):
            self._field_names = []
            for field_name, field in attributes.items():
                if isinstance(field, BaseField):
                    if field_name not in request and field.required:
                        raise ValidationError(f'Field "{field_name}" is required but not provided in request')
                    field_value = request.get(field_name)
                    field.__set__(self, field_value)
                    self._field_names.append(field_name)

            if hasattr(self, 'validate_values'):
                self.validate_values()

        return super().__new__(mcs, class_name, parents, {**attributes, '__init__': init})


class BaseRequest(metaclass=MetaRequest):
    pass


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

    def validate_values(self):
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


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

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
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
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
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
