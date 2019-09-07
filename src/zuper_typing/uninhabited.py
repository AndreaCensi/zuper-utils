class Unh:
    def __init__(self):
        raise Exception()  # pragma: no cover


def make_Uninhabited():
    return Unh


def is_Uninhabited(x):
    return x is Unh
