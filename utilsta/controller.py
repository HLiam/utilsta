# TODO: have the value and pressed listeners only call the callback func with 'pressed' or 'value' (and not the button) if they only have one arg

from typing import Callable, List

from objc_util import ObjCBlock, ObjCClass, ObjCInstance, c_void_p

from .exceptions import NoControllerConnectedError


# these are made into properties of `Input`
# 'objc_name': ('property_name', 'friendly_name')
_button_map = {
    'buttonA': ('a', 'A'),
    'buttonB': ('b', 'B'),
    'buttonX': ('x', 'X'),
    'buttonY': ('y', 'Y'),
    'leftTrigger':   ('lt', 'LT'),
    'rightTrigger':  ('rt', 'RT'),
    'leftShoulder':  ('lb', 'LB'),
    'rightShoulder': ('rb', 'RB'),
    'buttonMenu':    ('menu', 'MENU'),
    'buttonOptions': ('option', 'OPTION'),
    '_buttonHome':   ('home', 'HOME'),
    # these are for pushing the thumbsticks in like a button, not for moving them like a joystick
    'leftThumbstickButton':  ('lsp', 'LS PUSH'),
    'rightThumbstickButton': ('rsp', 'RS PUSH'),
}

_GCContoller = ObjCClass('GCController')
_ButtonInput = ObjCClass('GCControllerButtonInput')


class Input:
    def __init__(self, objc_input, name):
        self._inner = objc_input
        self.name = name

    def __repr__(self):
        return f'{self.__class__.__name__}(name={self.name}, controller={self.controller})'

    @property
    def controller(self):
        return Controller(self._inner.controller())


class Button(Input):
    def __init__(self, objc_button, name):
        super().__init__(objc_button, name)
        self._pressed_listener = None
        self._value_listener = None
        # these are needed to stop the handler blocks from having no references and being deleted
        self._pressed_handler_block = None
        self._value_handler_block = None

    def __repr__(self):
        return f'Button(name={self.name!r}, controller={self.controller!r}, pressed_changed_listener={self.pressed_changed_listener!r}, value_changed_listener={self.value_changed_listener!r})'

    @property
    def is_pressed(self) -> bool:
        return self._inner.isPressed()

    @property
    def value(self) -> float:
        return self._inner.value()

    @property
    def pressed_changed_listener(self) -> Callable:
        return self._pressed_listener

    @pressed_changed_listener.setter
    def pressed_changed_listener(self, f: Callable):

        def handler(_, button, pressed):
            button = Button(ObjCInstance(button), self.name)
            self._pressed_listener(button, pressed == 1)

        handler_block = ObjCBlock(
            handler,
            argtypes=[c_void_p, c_void_p, c_void_p])

        self._pressed_listener = f
        self._pressed_handler_block = handler_block
        self._inner.setPressedChangedHandler_(handler_block)

    @property
    def value_changed_listener(self) -> Callable:
        return self._value_listener

    @value_changed_listener.setter
    def value_changed_listener(self, f: Callable):

        def handler(_, button, _pressed):
            button = Button(ObjCInstance(button), self.name)
            self._value_listener(button, self.value)

        handler_block = ObjCBlock(
            handler,
            argtypes=[c_void_p, c_void_p, c_void_p])

        self._value_listener = f
        self._value_handler_block = handler_block
        self._inner.setValueChangedHandler_(handler_block)

    def remove_pressed_changed_listener(self):
        self.pressed_changed_listener = None

    def remove_value_changed_listener(self):
        self.value_change_listener = None

    def get_and_reset_times_pressed(self) -> int:
        return self._inner.getAndResetTimesPressed()

    def reset_times_pressed(self):
        self.get_and_reset_times_pressed()


class DirectionalInput(Input):
    def __init__(self, objc_input, name):
        super().__init__(objc_input, name)

    @property
    def x(self) -> float:
        return self._inner.xAxis().value()

    @property
    def y(self) -> float:
        return self._inner.yAxis().value()

    @property
    def y_axis(self):
        return Axis(self._inner.yAxis(), self.name + ' Y AXIS')

    @property
    def x_axis(self):
        return Axis(self._inner.xAxis(), self.name + ' X AXIS')

    @property
    def value(self) -> (float, float):
        return (self.x, self.y)

    @property
    def up(self) -> Button:
        return Button(self._inner.up(), self.name + ' UP')

    @property
    def down(self) -> Button:
        return Button(self._inner.down(), self.name + ' DOWN')

    @property
    def left(self) -> Button:
        return Button(self._inner.left(), self.name + ' LEFT')

    @property
    def right(self) -> Button:
        return Button(self._inner.right(), self.name + ' RIGHT')


class Axis(Input):
    def __init__(self, objc_axis, name, controller):
        super().__init__(objc_axis, name)
        self._value_listener = None
        self.value_handler_block = None
        # patch controller in because the objc `GCcontrolAxisInput` sets it to `None` fir some reason
        if isinstance(controller, Controller):
            self._inner.controller = lambda: controller._inner
        else:
            self._inner.controller = lambda: controller

    @property
    def value(self):
        return self._inner.value(r)

    @property
    def value_changed_listener(self) -> Callable:
        return self._value_listener

    @value_changed_listener.setter
    def value_changed_listener(self, f: Callable):

        def handler(_, button, _pressed):
            button = (ObjCInstance(button), self.name)
            self._value_listener(button, self.value)

        handler_block = ObjCBlock(
            handler,
            argtypes=[c_void_p, c_void_p, c_void_p])

        self._value_listener = f
        self._value_handler_block = handler_block
        self._inner.setValueChangedHandler_(handler_block)


class InputElements:
    """This class exists purly to enable `controller.input.a` syntax. It shouldn't be used directly.'"""
    def __init__(self, controller):
        self.controller = controller

    @property
    def ls(self):
        return DirectionalInput(self.controller._gamepad.leftThumbstick(), 'LS')

    @property
    def rs(self):
        return DirectionalInput(self.controller._gamepad.rightThumbstick(), 'RS')

    @property
    def dpad(self):
        return DirectionalInput(self.controller._gamepad.dpad(), 'DPAD')


# dynamically add properties to `Input`
for objc_name, (prop_name, friendly_name) in _button_map.items():
    def func_factory(objc_name=objc_name, prop_name=prop_name, friendly_name=friendly_name):
        @property
        def prop(self) -> Button:
            return Button(getattr(self.controller._gamepad, objc_name)(), friendly_name)
        return prop

    setattr(InputElements, prop_name, func_factory())


class Controller:
    def __init__(self, objc_controller):
        self._inner = objc_controller
        self._gamepad = self._inner.extendedGamepad()
        self.input = InputElements(self)

    def __repr__(self):
        return f'Controller(vendor={self.vendor!r}, device_hash={self.device_hash!r})'

    @property
    def vendor(self) -> str:
        return str(self._inner.vendorName())

    @property
    def device_hash(self) -> str:
        return self._inner.deviceHash()

    @property
    def is_attached_to_device(self):
        self._inner.isAttachedToDevice()

    @property
    def reports_absolute_dpad_values(self) -> bool:
        return self._inner.profile().reportsAbsoluteDpadValues()


def get_controllers() -> List[Controller]:
    return [Controller(c) for c in _GCContoller.controllers()]


def get_controller() -> Controller:
    try:
        return get_controllers()[0]
    except IndexError:
        raise NoControllerConnectedError

