from shared import _uidevice


_taptic_engine = _uidevice._tapticEngine()


def haptic_from_id(id: int):
    _taptic_engine.actuateFeedback_(id)

def pop():
    haptic_from_id(1)

def triple_knock():
    haptic_from_id(2)

