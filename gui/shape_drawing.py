from itertools import chain
from math import pi, sin, cos

import pyglet

from consts import *


def draw_line(point_1, point_2, color=WHITE):
    """
    Draws a line between two points on the screen.
    :param point_1: a tuple of (x, y) of the first point.
    :param point_2: the same for the other point.
    :param color: the color of the line.
    :return: None
    """
    vertex_view = 'v2i'
    if any([isinstance(coord, float) for coord in point_1 + point_2]):
        vertex_view = 'v2f'
    pyglet.graphics.draw(2, pyglet.gl.GL_LINES, (vertex_view, point_1 + point_2), ('c3B', color * 2))


def draw_rect_no_fill(x, y, width, height):
    """
    Draws an unfilled rectangle from the bottom left corner (x,y) with a width of
    `width` and a height of `height`.
    """
    int_x, int_y, int_width, int_height = map(int, (x, y, width, height))
    pyglet.graphics.draw(8, pyglet.gl.GL_LINES,
                         ('v2i', (int_x, int_y,
                                  int_x + int_width, int_y,
                                  int_x + int_width, int_y,
                                  int_x + int_width, int_y + int_height,
                                  int_x + int_width, int_y + int_height,
                                  int_x, int_y + int_height,
                                  int_x, int_y + int_height,
                                  int_x, int_y)),
                         ('c4B', (50, 50, 50, 10) * 8)
                         )


def draw_rect(x, y, width, height, color=GRAY):
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


def draw_rect_with_outline(x, y, width, height, color=GRAY, outline_color=WHITE, outline_width=DEFAULT_OUTLINE_WIDTH):
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
    draw_rect(x - outline_width/2, y - outline_width/2,
              width + outline_width, height + outline_width, color=outline_color)
    draw_rect(x, y, width, height, color=color)


def draw_pause_rectangles():
    """
    Draws two rectangles in the side of the window like a pause sign.
    This is called when the program is paused.
    :return: None
    """
    x, y = PAUSE_RECT_COORDINATES
    draw_rect(x, y, PAUSE_RECT_WIDTH, PAUSE_RECT_HEIGHT, RED)
    draw_rect(x + 2 * PAUSE_RECT_WIDTH, y, PAUSE_RECT_WIDTH, PAUSE_RECT_HEIGHT, RED)


def draw_circle(x, y, radius, color=WHITE):
    """
    Draws a circle with a given center location and a radius and a color.
    :return:
    """
    d_theta = (2 * pi) / CIRCLE_SEGMENT_COUNT
    vertices = list(chain(*[(x + radius * cos(i * d_theta), y + radius * sin(i * d_theta))
                            for i in range(0, CIRCLE_SEGMENT_COUNT)]))

    pyglet.graphics.draw(CIRCLE_SEGMENT_COUNT, pyglet.gl.GL_LINE_LOOP,
                         ('v2f', tuple(vertices)),
                         ('c3B', color * CIRCLE_SEGMENT_COUNT),
                         )
