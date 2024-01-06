def logger(function):
    def wrapper(*args, **kwargs):
        """wrapper documentation"""
        print(f"----- {function.__doc__}: start -----")
        output = function(*args, **kwargs)
        print(f"----- {function.__doc__}: end -----")
        return output
    return wrapper

@logger
def add_two_numbers(a, b):
    """this function adds two numbers"""
    return a + b

add_two_numbers(1,2)