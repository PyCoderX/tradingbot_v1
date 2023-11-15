from frozendict import frozendict
from functools import wraps


def freezeargs(func):
    """
    Transform mutable dictionnary  Into immutable
    Useful to be compatible with cache
    """

    @wraps(func)
    def wrapped(*args, **kwargs):
        args = tuple(frozendict(arg) if isinstance(arg, dict) else arg for arg in args)
        kwargs = {k: frozendict(v) if isinstance(v, dict) else v for k, v in kwargs.items()}
        return func(*args, **kwargs)

    return wrapped
