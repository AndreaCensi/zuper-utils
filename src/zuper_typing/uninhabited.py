class Unh:
    U = None


Unh.U = Unh()


def make_Uninhabited():
    return Unh.U


def is_Uninhabited(x):
    return x is Unh.U
