from objc_util import ObjCClass, ObjCBlock, ObjCInstance, c_void_p

from shared import _CMAltimeter


# we keep a reference to the currently used callback function so that it doesn't get deleted while in use
_active_handler = None

_NSOperationQueue = ObjCClass('NSOperationQueue')
_altimeter = _CMAltimeter.new()
_main_queue = _NSOperationQueue.mainQueue()


class AltimeterData:
    def __init__(self, altimeter_data):
        self.relative_altitude = altimeter_data.relativeAltitude().floatValue()
        self.pressure = altimeter_data.pressure().floatValue()
        self.timestamp = altimeter_data.timestamp()

    def __repr__(self):
        return f'BarometerData(relative_altitude={self.relative_altitude!r}, pressure={self.pressure!r}, timestamp={self.timestamp!r})'

    def __format__(self, spec):
        if spec[0] == 'a':
            value = self.relative_altitude
        elif spec[0] == 'p':
            value = self.pressure
        elif spec[0] == 't':
            value = self.timestamp
        return format(value, spec[1:])


class Start:
    """This is returned by `start` so that it can be used as a context manager."""
    def __enter__(self):
        # the call to `start` will have already started the altimeter
        pass

    def __exit__(self, *_):
        stop()


def has_permission() -> bool:
    return _CMAltimeter.authorizationStatus()


def is_running() -> bool:
    return _active_handler is not None


def start(callback) -> Start:
    """The return value should only be used as a context manager."""
    global _active_handler

    if is_running:
        raise AlreadyRunningError
    is_running = True

    def handler(_cmd, data, _err):
        callback(AltimeterData(ObjCInstance(data)))

    handler_block = ObjCBlock(
        handler,
        argtypes=[c_void_p, c_void_p, c_void_p])
    _active_handler = handler_block
    _altimeter.startRelativeAltitudeUpdatesToQueue_withHandler_(_main_queue, handler_block)
    return Start()


def stop():
    global _active_handler
    _altimeter.stopRelativeAltitudeUpdates()
    _active_handler = None

