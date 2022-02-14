from functools import wraps


def optional_arg_decorator(decorator):
    @wraps(decorator)
    def wrapped_decorator(*args, **kwargs):
        if len(args) == 1:
            return decorator(args[0])

        else:
            def real_decorator(function):
                return decorator(function, *args, **kwargs)

            return real_decorator

    return wrapped_decorator
