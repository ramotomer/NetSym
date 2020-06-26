from computing.computer import Computer
# from computing.nat import NAT
from computing.router import Router
from computing.switch import Switch, Hub, Antenna
# from computing.internet import Internet
from consts import *
from gui.user_interface.popup_windows.image_button import ImageButton
from gui.user_interface.popup_windows.popup_window import PopupWindow
from usefuls import with_args, called_in_order


class DeviceCreationWindow(PopupWindow):
    """
    This is a popup window that allows you to create a device in your network.
    """

    DEVICE_TO_IMAGE = {
        Computer: (COMPUTER_IMAGE, "(n)"),
        Switch: (SWITCH_IMAGE, "(s)"),
        Router: (ROUTER_IMAGE, "(r)"),
        Hub: (HUB_IMAGE, "(h)"),
        Antenna: (ANTENNA_IMAGE, "(a)"),
        # NAT: (NAT_IMAGE, "(alt+n)"),
        # Internet: (INTERNET_IMAGE, "(alt+i)"),
    }

    def __init__(self, user_interface):
        """
        Initiates the window.
        """
        width = len(self.DEVICE_TO_IMAGE) * (DEVICE_CREATION_BUTTON_SIZE + DEVICE_CREATION_BUTTON_GAP) - DEVICE_CREATION_BUTTON_GAP
        height = TEXTBOX_HEIGHT
        x, y = WINDOW_WIDTH / 2 - width / 2, WINDOW_HEIGHT / 2 - height / 2
        buttons = [
            ImageButton(
                x + i * (DEVICE_CREATION_BUTTON_SIZE + DEVICE_CREATION_BUTTON_GAP),
                y,
                called_in_order(
                    with_args(user_interface.create_device, device),
                    self.delete,
                ),
                self.DEVICE_TO_IMAGE[device][0],
                f"{device.__name__} {self.DEVICE_TO_IMAGE[device][1]}",
                width=DEVICE_CREATION_BUTTON_SIZE, height=DEVICE_CREATION_BUTTON_SIZE,
                key=user_interface.key_from_string(self.DEVICE_TO_IMAGE[device][1]),
            ) for i, device in enumerate(self.DEVICE_TO_IMAGE)
        ]

        super(DeviceCreationWindow, self).__init__(
            x, y,
            "Pick a device to create:",
            user_interface,
            buttons,
            width, height,
            color=PINK,
            title="create a device!",
        )
