def first_exp():
    MyShinyClass = type('MyShinyClass', (), {})
    print(MyShinyClass)
    FooChild = type('FooChild', (MyShinyClass,), {})
    print(FooChild)


def upper_attr(future_class_name, future_class_parents, future_class_attr):
    attrs = ((name, value) for name, value in future_class_attr.items() if not name.startswith('__'))
    uppercase_attr = dict((name.upper(), value) for name, value in attrs)

    return type(future_class_name, future_class_parents, uppercase_attr)


class Foo(object):
    # или можно определить __metaclass__ здесь, чтобы сработало только для этого класса
    __metaclass__ = upper_attr
    bar = 'bip'


class UpperAttrMetaclass(type):

    def __new__(cls, name, bases, dct):
        attrs = ((name, value) for name, value in dct.items() if not name.startswith('__'))
        uppercase_attr = dict((name.upper(), value) for name, value in attrs)

        return super(UpperAttrMetaclass, cls).__new__(cls, name, bases, uppercase_attr)


if __name__ == '__main__':
    first_exp()

    print(hasattr(Foo, 'bar'))
    # Out: False
    print(hasattr(Foo, 'BAR'))
    # Out: True

    f = Foo()
    print(f)
    # Out: 'bip'
