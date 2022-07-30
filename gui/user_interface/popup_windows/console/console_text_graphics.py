from consts import TEXT, CONSOLE
from gui.user_interface.text_graphics import Text


class ConsoleTextGraphics(Text):
    """
    A graphics object that holds the text of a console.
    The main difference is that the padding changes in accordance with the size of the console :)
    """
    def __init__(self, text, x, y,
                 console_graphics,
                 start_hidden=True,
                 font_size=TEXT.FONT.DEFAULT_SIZE,
                 align=TEXT.ALIGN.LEFT,
                 color=CONSOLE.TEXT_COLOR,
                 font=TEXT.FONT.DEFAULT):
        super(ConsoleTextGraphics, self).__init__(
            text, x, y, console_graphics,
            is_button=False,
            start_hidden=start_hidden,
            max_width=console_graphics.width,
            font_size=font_size,
            align=align,
            color=color,
            font=font,
        )

    @property
    def console_graphics(self):
        return self.parent_graphics
        
    @property
    def padding(self):
        return (self.console_graphics.width / 2) + 2, self.console_graphics.height
