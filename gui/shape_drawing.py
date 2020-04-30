import pyglet
from consts import *
from math import pi, sin, cos
from itertools import chain


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
    ix, iy, iwidth, iheight = map(int, (x, y, width, height))
    pyglet.graphics.draw(8, pyglet.gl.GL_LINES,
                         ('v2i', (ix, iy,
                                  ix + iwidth, iy,
                                  ix + iwidth, iy,
                                  ix + iwidth, iy + iheight,
                                  ix + iwidth, iy + iheight,
                                  ix, iy + iheight,
                                  ix, iy + iheight,
                                  ix, iy)),
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
    :return: None
    """
    ix, iy, iwidth, iheight = map(int, (x, y, width, height))
    pyglet.graphics.draw(4, pyglet.gl.GL_QUADS,
                         ('v2i', (ix, iy,
                                  ix + iwidth, iy,
                                  ix + iwidth, iy + iheight,
                                  ix, iy + iheight)),
                         ('c3B', color * 4)
                         )


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
    vertices = list(chain(*[(x + radius * cos(i * d_theta), y + radius * sin(i * d_theta)) for i in range(0, CIRCLE_SEGMENT_COUNT)]))

    pyglet.graphics.draw(CIRCLE_SEGMENT_COUNT, pyglet.gl.GL_LINE_LOOP,
                         ('v2f', tuple(vertices)),
                         ('c3B', color * CIRCLE_SEGMENT_COUNT),
                         )
