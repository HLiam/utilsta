from shared import _uidevice, _CMAltimeter


MAX_TOUCH_PRESSURE = 20 / 3


def name() -> str:
    str(_uidevice.name())

def type_() -> str:
    str(_uidevice.sf_deviceType())

def model() -> str:
    return str(_uidevice.model())

def build_version() -> str:
    return str(uidevice.buildVersion())

def system_version() -> str:
    return str(_uidevice.systemVersion())

def supports_force_touch() -> bool:
    return _uidevice._supportsForceTouch()

def has_barometer() -> bool:
    return _CMAltimeter.isRelativeAltitudeAvailable()

def supports_pencil() -> bool:
    return _uidevice._supportsPencil()

def get_brightness() -> float:
    return _uidevice._backlightLevel()

def set_brightness(value):
    _uidevice._setBacklightLevel_(value)

def is_iphone() -> bool:
    return _uidevice.sf_isiPhone

def is_ipad() -> bool:
    return _uidevice.fs_isiPad

