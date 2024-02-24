class BaseField:
    value: object


# class MetaRequest(type):
#     def __call__(self, *args, **kwargs):
#         self.fields = dict(kwargs)
#         return super().__call__(*args, **kwargs)

    # error_messages = {}
    # error_exception: bool = False  # True - raise Exception, False - add to error_messages
    #
    # def __new__(mcls, name, bases, attrs):
    #     mcls.field_classes: dict = {}
    #     print("__new__")
    #     print(type(attrs))
    #     for key, value in attrs.items():
    #         if isinstance(value, BaseField):
    #             mcls.field_classes[key] = value
    #
    #
    #     print(mcls.field_classes)
    #     return type.__new__(mcls, name, bases, attrs)
    #
    #
    # # def __call__(self,*args, **kwargs):
    # #     print('call')
    # #     for key, value in kwargs.items():
    # #         print(key, value)
    # #         if isinstance(key, BaseField):
    # #             self.field_classes[key] = value
    # #     # self.field_classes = {
    # #     #     f for f in self.__dict__ if isinstance(self.__dict__.get(f), BaseField)
    # #     # }
    # #     print("self.field_classes",self.field_classes)
    # #     return super().__call__(*args, **kwargs)
    #
    # def __iter__(cls):
    #     return iter(cls.field_classes)

# class RegisterLeafClasses(type):
#     def __init__(cls, name, bases, nmspc):
#         super(RegisterLeafClasses, cls).__init__(name, bases, nmspc)
#         if not hasattr(cls, 'registry'):
#             cls.registry = set()
#         cls.registry.add(cls)
#         cls.registry -= set(bases)  # Remove base classes
#
#     # Metamethods, called on class objects:
#     def __iter__(cls):
#         return iter(cls.registry)
#
#     def __str__(cls):
#         if cls in cls.registry:
#             return cls.__name__
#         return cls.__name__ + ": " + ", ".join([sc.__name__ for sc in cls])
#
class MetaRequest(type):
    '''
    Creates fields attribute as tuple with the Field type class attributes
    '''
    def __new__(mcls, name, bases, attrs):
        attrs['fields'] = tuple(atr for atr in attrs if isinstance(attrs.get(atr), BaseField))
        return super().__new__(mcls, name, bases, attrs)


class Request(metaclass=MetaRequest):
    context = {}
    store = None

    def __init__(self, **kwargs):
        for atr in self.fields:
            getattr(self, atr).value = kwargs.get(atr, None)


    def isvalid(self):
        self.errorfields = []
        for atr in self.fields:
            try:
                getattr(self, atr).isvalid()
            except (ValueError, TypeError) as error:
                self.errorfields.append((atr, error))
        return not self.errorfields
class BadType(Request):
    a=BaseField()
    b=BaseField()
    d=BaseField()
    c=0





    def __repr__(self):
        attributes = {
            name: getattr(self, name)
            for name in self.__dict__
            if name[0:2] != '__'
        }
        return f'<Class {self.__class__.__name__}: {attributes}>'


r = BadType(a=4,b="3",c=0,d=5)

print(r)
print(r.a)
print(r.fields[0])
print(r.__dict__)
