class SuperMeta(type):
    def __call__(meta, classname, supers, classdict):
        print('SuperMeta call:', classname, supers, classdict, sep='\n...')
        return type.__call__(meta, classname, supers, classdict)

    def __init__(Class, classname, supers, classdict):
        print('SuperMeta init:', classname, supers, classdict,
              f'init class object: {Class.__dict__.keys()}',
              sep='\n...')


print('----------making metaclass')


class SubMeta(type, metaclass=SuperMeta):
    def __new__(meta, classname, supers, classdict):
        print('SubMeta call:', classname, supers, classdict, sep='\n...')
        return type.__new__(meta, classname, supers, classdict)

    def __init__(Class, classname, supers, classdict):
        print('SubMeta init:', classname, supers, classdict,
              f'init class object: {Class.__dict__.keys()}',
              sep='\n...')


class Egg:
    pass


print('----------making class')


class Spam(Egg, metaclass=SubMeta):
    data = 1

    def meth(self, arg):
        return self.data + arg


print('make instance')
ii = Spam()
print('ii', ii.data, ii.meth(2), sep='\n...')
