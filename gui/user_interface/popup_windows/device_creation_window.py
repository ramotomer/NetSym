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
        Computer: (IMAGES.COMPUTERS.COMPUTER, "(n)"),
        Switch: (IMAGES.COMPUTERS.SWITCH, "(s)"),
        Router: (IMAGES.COMPUTERS.ROUTER, "(r)"),
        Hub: (IMAGES.COMPUTERS.HUB, "(h)"),
        Antenna: (IMAGES.COMPUTERS.ANTENNA, "(a)"),
        # NAT: (IMAGES.COMPUTERS.NAT, "(alt+n)"),
        # Internet: (IMAGES.COMPUTERS.INTERNET, "(alt+i)"),
    }

    def __init__(self, user_interface):
        """
        Initiates the window.
        """
        width = len(self.DEVICE_TO_IMAGE) * (WINDOWS.POPUP.DEVICE_CREATION.BUTTON_SIZE + WINDOWS.POPUP.DEVICE_CREATION.BUTTON_GAP) - WINDOWS.POPUP.DEVICE_CREATION.BUTTON_GAP
        height = WINDOWS.POPUP.TEXTBOX.HEIGHT
        x, y = WINDOWS.MAIN.WIDTH / 2 - width / 2, WINDOWS.MAIN.HEIGHT / 2 - height / 2
        buttons = [
            ImageButton(
                x + i * (WINDOWS.POPUP.DEVICE_CREATION.BUTTON_SIZE + WINDOWS.POPUP.DEVICE_CREATION.BUTTON_GAP),
                y,
                called_in_order(
                    with_args(user_interface.create_device, device),
                    self.delete,
                ),
                self.DEVICE_TO_IMAGE[device][0],
                f"{device.__name__} {self.DEVICE_TO_IMAGE[device][1]}",
                width=WINDOWS.POPUP.DEVICE_CREATION.BUTTON_SIZE, height=WINDOWS.POPUP.DEVICE_CREATION.BUTTON_SIZE,
                key=user_interface.key_from_string(self.DEVICE_TO_IMAGE[device][1]),
            ) for i, device in enumerate(self.DEVICE_TO_IMAGE)
        ]

        super(DeviceCreationWindow, self).__init__(
            x, y,
            "Pick a device to create:",
            user_interface,
            buttons,
            width, height,
            color=COLORS.PINK,
            title="create a device!",
        )
