from __future__ import annotations

from contextlib import contextmanager
from itertools import chain
from operator import itemgetter
from typing import Optional, Generator

from consts import *
from exceptions import *
from usefuls.funcs import circular_coordinates, sine_wave_coordinates, lighten_color, darken_color, \
    normal_color_to_weird_gl_color

drawing_parameters = {
    'line_width': 1.0,
}
pyglet.gl.glLineWidth(drawing_parameters['line_width'])


def _set_line_width(value: float) -> None:
    """
    Sets the width of all lines drawn from this point onward
    """
    drawing_parameters['line_width'] = value
    pyglet.gl.glLineWidth(value)


@contextmanager
def temporary_line_width(value: float) -> Generator[None]:
    """
    A contextmanager that temporarily sets the value of the width of lines
    """
    previous_line_width = drawing_parameters['line_width']
    _set_line_width(value)

    try:
        yield None
    finally:
        _set_line_width(previous_line_width)


def draw_line(point_1: Tuple[float, float], point_2: Tuple[float, float], color: T_Color = COLORS.WHITE, width: float = 1.0) -> None:
    """
    Draws a line between two points on the screen.
    :param width:
    :param point_1: a tuple of (x, y) of the first point.
    :param point_2: the same for the other point.
    :param color: the color of the line.
    :return: None
    """
    vertex_view = 'v2i'
    if any([isinstance(coord, float) for coord in point_1 + point_2]):
        vertex_view = 'v2f'

    with temporary_line_width(width):
        pyglet.graphics.draw(2, pyglet.gl.GL_LINES, (vertex_view, point_1 + point_2), ('c3B', color * 2))


def draw_rectangle(
        x: float, y: float,
        width: float, height: float,
        color: Optional[T_Color] = None, outline_color: Optional[T_Color] = None,
        outline_width: float = SHAPES.RECT.DEFAULT_OUTLINE_WIDTH) -> None:
    """
    Draws a rectangle.
    :param x:
    :param y: bottom left corner coordinates
    :param width:
    :param height: size of the square
    :param color: the fill color, if None, no fill
    :param outline_color: the outline color, if None, no outline
    :param outline_width: ...
    :return:
    """
    if color is not None and outline_color is not None:
        _draw_rect_with_outline(x, y, width, height, color, outline_color, outline_width)

    elif color is not None:
        _draw_rect_no_outline(x, y, width, height, color)

    elif outline_color is not None:
        _draw_rect_no_fill(x, y, width, height, outline_color, outline_width)

    else:
        _draw_rect_no_outline(x, y, width, height)


def _draw_rect_no_fill(x: float, y: float, width: float, height: float, color: T_Color = COLORS.WHITE, outline_width: float = 1.0) -> None:
    """
    Draws an unfilled rectangle from the bottom left corner (x,y) with a width of
    `width` and a height of `height`.
    """
    int_x, int_y, int_width, int_height = map(int, (x, y, width, height))
    color = color + (0,)

    with temporary_line_width(outline_width):
        pyglet.graphics.draw(8, pyglet.gl.GL_LINES,
                             ('v2i', (int_x, int_y,
                                      int_x + int_width, int_y,
                                      int_x + int_width, int_y,
                                      int_x + int_width, int_y + int_height,
                                      int_x + int_width, int_y + int_height,
                                      int_x, int_y + int_height,
                                      int_x, int_y + int_height,
                                      int_x, int_y)),
                             ('c4B', color * 8)
                             )


def _draw_rect_no_outline(x: float, y: float, width: float, height: float, color: T_Color = COLORS.GRAY) -> None:
    """
    Draws a filled rectangle from the bottom left corner (x, y) with a width of
    `width` and a height of `height`.
    :param x:
    :param y: coordinates of the bottom left corner of the rectangle.
    :param width:
    :param height:
    :param color:
    :return: None
    """
    int_x, int_y, int_width, int_height = map(int, (x, y, width, height))
    pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                         ('v2i', (int_x, int_y,
                                  int_x + int_width, int_y,
                                  int_x + int_width, int_y + int_height,
                                  int_x, int_y + int_height)),
                         ('c3B', color * 4)
                         )


def _draw_rect_with_outline(x: float, y: float, width: float, height: float,
                            color: T_Color = COLORS.GRAY, outline_color: T_Color = COLORS.WHITE,
                            outline_width: float = SHAPES.RECT.DEFAULT_OUTLINE_WIDTH) -> None:
    """
    Draws a rectangle with an outline.
    :param x:
    :param y:
    :param width:
    :param height:
    :param color:
    :param outline_color:
    :param outline_width:
    :return:
    """
    _draw_rect_no_outline(
        x - outline_width/2, y - outline_width/2,
        width + outline_width, height + outline_width,
        color=outline_color
    )
    _draw_rect_no_outline(
        x, y, width, height, color=color
    )


def draw_rect_by_corners(point1: Tuple[float, float], point2: Tuple[float, float],
                         color: Optional[T_Color] = None, outline_color: Optional[T_Color] = None,
                         outline_width: Optional[float] = None) -> None:
    """
    Receives two points and draws a rect
    """
    x1, y1 = point1
    x2, y2 = point2
    points = [point1, point2, (x1, y2), (x2, y1)]
    sorted_points = list(sorted(sorted(points, key=itemgetter(0)), key=itemgetter(1)))
    (bottom_left_x, bottom_left_y), (upper_right_x, upper_right_y) = sorted_points[0], sorted_points[-1]
    draw_rectangle(bottom_left_x, bottom_left_y,
                   (upper_right_x - bottom_left_x), (upper_right_y - bottom_left_y),
                   color, outline_color, outline_width)


def draw_pause_rectangles() -> None:
    """
    Draws two rectangles in the side of the window like a pause sign.
    This is called when the program is paused.
    :return: None
    """
    x, y = SHAPES.PAUSE_RECT.COORDINATES
    _draw_rect_no_outline(x, y, SHAPES.PAUSE_RECT.WIDTH, SHAPES.PAUSE_RECT.HEIGHT, COLORS.RED)
    _draw_rect_no_outline(x + 2 * SHAPES.PAUSE_RECT.WIDTH, y, SHAPES.PAUSE_RECT.WIDTH, SHAPES.PAUSE_RECT.HEIGHT, COLORS.RED)


def draw_tiny_corner_windows_icon() -> None:
    """
    Draws the four blue squares in the corner that indicate that the screen is highlighted and currently ignores presses of `winkey` etc...
    """
    SIZE = 10
    GAP_SIZE = 2
    INITIAL_X = 5
    INITIAL_Y_FROM_TOP = 15
    SQUARE_COLOR = COLORS.BLUE

    draw_rectangle(INITIAL_X,                   WINDOWS.MAIN.HEIGHT - INITIAL_Y_FROM_TOP,                     SIZE, SIZE, SQUARE_COLOR)
    draw_rectangle(INITIAL_X + SIZE + GAP_SIZE, WINDOWS.MAIN.HEIGHT - INITIAL_Y_FROM_TOP,                     SIZE, SIZE, SQUARE_COLOR)
    draw_rectangle(INITIAL_X,                   WINDOWS.MAIN.HEIGHT - (INITIAL_Y_FROM_TOP + SIZE + GAP_SIZE), SIZE, SIZE, SQUARE_COLOR)
    draw_rectangle(INITIAL_X + SIZE + GAP_SIZE, WINDOWS.MAIN.HEIGHT - (INITIAL_Y_FROM_TOP + SIZE + GAP_SIZE), SIZE, SIZE, SQUARE_COLOR)


def draw_circle(x: float, y: float, radius: float,
                outline_color: T_Color = COLORS.WHITE, fill_color: Optional[T_Color] = None) -> None:
    """
    Draws a circle with a given center location and a radius and a color.
    :return:
    """
    if fill_color is not None:
        pyglet.gl.glColor3f(*normal_color_to_weird_gl_color(fill_color, False))
        pyglet.gl.glLoadIdentity()
        pyglet.gl.glBegin(pyglet.gl.GL_POLYGON)
        for cx, cy in circular_coordinates((x, y), radius, SHAPES.CIRCLE.SEGMENT_COUNT):
            pyglet.gl.glVertex2f(cx, cy)
        pyglet.gl.glEnd()

    vertices = list(chain(*circular_coordinates((x, y), radius, SHAPES.CIRCLE.SEGMENT_COUNT)))
    pyglet.graphics.draw(SHAPES.CIRCLE.SEGMENT_COUNT, pyglet.gl.GL_LINE_LOOP,
                         ('v2f', tuple(vertices)),
                         ('c3B', outline_color * SHAPES.CIRCLE.SEGMENT_COUNT),
                         )


def draw_point(x: float, y: float, color: T_Color, width: float = 1) -> None:
    """
    Draws a point at the specified location
    """
    if width > 15:
        raise WrongUsageError("Use draw_circle! your point is too big!")
    draw_circle(x, y, width, color, color)


def debug_circle(x: float, y: float, fill_color: T_Color = COLORS.RED, size: float = 6) -> None:
    """
    Red dot for debugging
    """
    draw_point(x, y, fill_color)
    draw_circle(x, y, size, outline_color=fill_color)


def draw_sine_wave(start_coordinates: Tuple[float, float], end_coordinates: Tuple[float, float],
                   amplitude: float = SHAPES.SINE_WAVE.DEFAULT_AMPLITUDE,
                   frequency: float = SHAPES.SINE_WAVE.DEFAULT_FREQUENCY,
                   color: T_Color = CONNECTIONS.COLOR) -> None:
    """

    :param start_coordinates:
    :param end_coordinates:
    :param amplitude:
    :param frequency:
    :param color:
    :return:
    """
    vertices = list(chain(*sine_wave_coordinates(start_coordinates, end_coordinates,
                                                 amplitude, frequency)))
    length = len(vertices) // 2
    pyglet.graphics.draw(
        length,
        pyglet.gl.GL_LINE_STRIP,
        ('v2f', tuple(vertices)),
        ('c3B', color * length),
    )


def draw_button(x: float, y: float, width: float, height: float,
                color=BUTTONS.COLOR,
                outline_width: float = BUTTONS.OUTLINE_WIDTH) -> None:
    """
    Draws a button.
    :param x:
    :param y:
    :param width:
    :param height:
    :param color:
    :param outline_width:
    :return:
    """
    # button outline
    draw_rectangle(x - outline_width, y - outline_width,
                   width + (2 * outline_width), height + (2 * outline_width), color=BUTTONS.OUTLINE_COLOR)

    # button light (left) shadow
    draw_rectangle(x, y, width, height, color=lighten_color(color))

    # button dark (right) shadow
    draw_rectangle(x + BUTTONS.SHADOW_WIDTH, y, width - BUTTONS.SHADOW_WIDTH,
                   height - BUTTONS.SHADOW_WIDTH, color=darken_color(color))

    # button middle
    draw_rectangle(x + BUTTONS.SHADOW_WIDTH, y + BUTTONS.SHADOW_WIDTH,
                   width - (2 * BUTTONS.SHADOW_WIDTH), height - (2 * BUTTONS.SHADOW_WIDTH), color=color)
