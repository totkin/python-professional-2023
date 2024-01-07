from datetime import datetime


def first_func():
    selection = (int, str)
    print(f'selection:{selection}')


def temp_(value):
    try:
        datetime.strptime(value, '%d.%m.%Y')
    except ValueError:
        print(f'The value <{value}> should be date with DD.MM.YYYY format')
    return value


class BaseField:
    def __init__(self,
                 value: object | None = None,
                 value_type: object | None = str,
                 required: bool | None = False,
                 nullable: bool | None = True, ) -> None:
        self.required = required
        self.nullable = nullable
        self.value_type = value_type
        self.value = self._is_valid(value=value, value_type=value_type)

    def _is_valid(self, value, value_type: object | None):
        if not isinstance(value_type, tuple):
            value_type = (value_type,)
        value_validate = False
        for t in value_type:
            if isinstance(value, t):
                value_validate = True
        if not value_validate:
            raise ValueError(f'The field type must be in {value_type}')

        if self.required and value is None:
            raise ValueError(f'The field {type(self).__name__} is required')

        if not self.nullable and value in ('', [], (), {}):
            raise ValueError('The field should not be empty')

        return value

    def __repr__(self):
        attributes = {
            name: getattr(self, name)
            for name in self.__dict__
            if name[0:1] != '_'
        }
        return f'<Class {self.__class__.__name__}: {attributes}>'


class CharField(BaseField):
    def __init__(self,
                 value: object | None = None,
                 required: bool | None = False,
                 nullable: bool | None = True, ):
        super().__init__(value, required=required, nullable=nullable)


class PhoneField(BaseField):
    def __init__(self,
                 value: object | None = None,
                 required: bool | None = False,
                 nullable: bool | None = True, ):
        super().__init__(value, value_type=(int, str), required=required, nullable=nullable)

    def _is_valid(self, value, value_type):
        super()._is_valid(value, value_type)
        if not str(value)[0] == '7':
            raise ValueError(f'The field first symbol is {str(value)[0]} != 7')
        if len(str(value)) != 11:
            raise ValueError(f'The field length is {len(str(value))} != 11')
        return value


def getmethods(arg):
    print(f'getmetod({arg})')


class Extras(type):
    def __init__(cls, *args, **kwargs):
        cls.pi = getmethods


class GetClass(metaclass=Extras):
    def __init__(self, arg):
        pass


if __name__ == '__main__':
    # temp_('01.06.d24')
    temp = CharField(value='rest', nullable=False)
    print(f'temp: {temp}')
    # print(isinstance((int, str), tuple))
    # brom = GetClass('test')
    # brom.pi(arg='bust')
    print(f'__dir__:{temp.__dir__()}')
    print(f'__dict__:{temp.__dict__}')

    temp_ph = PhoneField(value=79123456789, required=True)
    print(f'temp_ph: {temp_ph}')

    pass
