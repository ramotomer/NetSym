# from computing.router import Router
# from gui.tech.computer_graphics import ComputerGraphics
# from consts import *
#
#
# class Internet(Router):
#     """
#     The internet is regarded here as one large router shaped like a cloud
#     It will not route private ip addresses
#     """
#     def __init__(self):
#         super(Internet, self).__init__("The Internet", is_dhcp_server=False)
#         self.os = None
#
#     def show(self, x, y):
#         """
#         overrides Computer.show and shows the same computer_graphics object only
#         with a router's photo.
#         :param x:
#         :param y:
#         :return: None
#         """
#         self.graphics = ComputerGraphics(x, y, self, INTERNET_IMAGE, scale_factor=INTERNET_SCALE_FACTOR)
