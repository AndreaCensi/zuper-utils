import functools
import os
from contextlib import contextmanager

from zuper_ipce.register import IPFSDagRegister, ConcreteRegister, use_register


def with_private_register(f):
    def f2(*args, **kwargs):
        with private_register(f.__name__):
            return f(*args, **kwargs)

    f2.__name__ = f.__name__
    return f2


r = IPFSDagRegister()


@functools.lru_cache(128)
def get_test_register(fn):
    # print(f'Creating new register {fn}')

    register = ConcreteRegister(fn, parent=r)

    return register


@contextmanager
def private_register(name):
    delete = False
    d = '.registers'
    if not os.path.exists(d):  # pragma: no cover
        os.makedirs(d)

    fn = os.path.join(d, f'{name}.db')

    if delete:  # pragma: no cover
        if os.path.exists(fn):
            os.unlink(fn)
    register = get_test_register(fn)
    with use_register(register):
        yield
