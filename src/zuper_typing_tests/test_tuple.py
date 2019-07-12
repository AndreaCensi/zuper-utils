from zuper_typing.annotations_tricks import make_Tuple


def test_making():
    make_Tuple()
    make_Tuple(int)
    make_Tuple(int, float)
    make_Tuple(int, float, bool)
    make_Tuple(int, float, bool, str)
    make_Tuple(int, float, bool, str, bytes)
    make_Tuple(int, float, bool, str, bytes, int)
