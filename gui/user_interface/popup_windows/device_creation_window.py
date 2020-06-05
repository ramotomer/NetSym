from computing.computer import Computer
from computing.router import Router
from computing.switch import Switch, Hub, Antenna
from consts import *
from gui.user_interface.popup_windows.image_button import ImageButton
from gui.user_interface.popup_windows.popup_window import PopupWindow
from usefuls import with_args, called_in_order


class DeviceCreationWindow(PopupWindow):
    """
    This is a popup window that allows you to create a device in your network.
    """

    DEVICE_TO_IMAGE = {
        Computer: COMPUTER_IMAGE,
        Switch: SWITCH_IMAGE,
        Router: ROUTER_IMAGE,
        Hub: HUB_IMAGE,
        Antenna: ANTENNA_IMAGE,
    }

    def __init__(self, user_interface):
        """
        Initiates the window.
        """
        width = len(self.DEVICE_TO_IMAGE) * (DEVICE_CREATION_BUTTON_SIZE + DEVICE_CREATION_BUTTON_GAP) - DEVICE_CREATION_BUTTON_GAP
        height = TEXTBOX_HEIGHT
        x, y = TEXTBOX_COORDINATES
        buttons = [
            ImageButton(
                x + i * (DEVICE_CREATION_BUTTON_SIZE + DEVICE_CREATION_BUTTON_GAP),
                y,
                called_in_order(
                    with_args(user_interface.create_device, device),
                    self.delete,
                ),
                self.DEVICE_TO_IMAGE[device],
                device.__name__,
                width=DEVICE_CREATION_BUTTON_SIZE, height=DEVICE_CREATION_BUTTON_SIZE,
            ) for i, device in enumerate(self.DEVICE_TO_IMAGE)
        ]

        super(DeviceCreationWindow, self).__init__(
            *TEXTBOX_COORDINATES,
            "Pick a device to create:",
            user_interface,
            buttons,
            width, height,
            color=PINK,
            title="create a device!",
        )
