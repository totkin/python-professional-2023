import logging
from abc import ABC, abstractmethod
from optparse import OptionParser


class ProtoField(ABC):
    # None must be in first position
    _empty_values: list = (None, '', [], (), {},)
    _type: object | None = str
    _value: object | None

    required: bool | None = False
    nullable: bool | None = True

    @property
    def value(self, ):
        return self._value

    @value.setter
    def value(self, loc_val):
        self._value = self._is_valid(loc_val)

    @property
    def type_name(self):
        return self._type.__name__.replace("<class ", "").replace(">", "")

    @abstractmethod
    def _is_valid(self, value) -> object | None:
        if value not in self._empty_values:
            result = self._is_valid_add(value)
        else:
            result = value
        return result

    @abstractmethod
    def _is_valid_add(self, value):
        pass

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

    def _is_valid(self, value) -> object | None:

        if self.required and value in self._empty_values[0]:
            str_error = f'The field {type(self).__name__} is required'
            logging.exception(str_error)
            raise ValueError()

        if not self.nullable and value in self._empty_values:
            raise ValueError('The field cannot be empty')

        if not isinstance(value, self._type):
            str_error = f'The field type must be one of the specified type(s) {self.type_name}'
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


class CharField(BaseField):
    """строĸа"""
    pass


class ArgumentsField(BaseField):
    """словарь (объеĸт в терминах json)"""
    _type = dict


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()

    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S')

    exp = CharField(required=False, nullable=True)
    exp.value = "Test"
    print(f'exp:{exp}')
    print(f'exp:{exp.value}')
