from zuper_typing.uninhabited import is_Uninhabited, make_Uninhabited


def test_uninhabited1():
    U = make_Uninhabited()
    assert is_Uninhabited(U)
