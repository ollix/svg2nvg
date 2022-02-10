# Copyright (c) 2014 Olli Wang. All right reserved.
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import re
import sys

from svgelements import svgelements

class Generator(object):

    def __init__(self, stmts, context='context'):
        self.context = context
        self.stmts = stmts
        self.new_paint = True

        self.transform_counts = []

    def __append_stmt(self, *args):
        stmt = self.__gen_stmt(*args)
        self.stmts.append(stmt)

    def __append_stmts(self, stmts):
        for stmt in stmts:
            self.__append_stmt(*stmt)

    def __gen_stmt(self, *args):
        command = args[0]
        if len(args) == 1:
            stmt = 'nvg%s(%s);' % (command, self.context)
        else:
            args = tuple(str(arg) for arg in args[1:])
            stmt = 'nvg%s(%s, %s);' % (command, self.context, ', '.join(args))
        return stmt

    def arc_to(self, x1, y1, x2, y2, radius):
        self.__append_stmt('ArcTo', x1, y1, x2, y2, radius)

    def begin_path(self):
        self.__append_stmt('BeginPath')

    def bezier_to(self, c1x, c1y, c2x, c2y, x, y):
        self.__append_stmt('BezierTo', c1x, c1y, c2x, c2y, x, y)

    def circle(self, cx, cy, r):
        self.__append_stmt('Circle', cx, cy, r)

    def close_path(self):
        self.__append_stmt('ClosePath')

    def ellipse(self, cx, cy, rx, ry):
        self.__append_stmt('Ellipse', cx, cy, rx, ry)

    def fill(self):
        self.__append_stmt('Fill')

    def fill_color(self, red, green, blue, alpha):
        self.__append_stmt('FillColor', self.get_color(red, green, blue, alpha))

    def fill_color(self, color):
        color = self.get_color_by_object(color)
        self.__append_stmt('FillColor', color)

    def get_color(self, red, green, blue, alpha):
        return 'nvgRGBA({}, {}, {}, {})'.format(red, green, blue, alpha)

    def get_color_by_object(self, color):
        if color is None or not isinstance(color, svgelements.Color) or \
           not color.opacity:
            return self.get_color(0, 0, 0, 0)
        return 'nvgRGBA({}, {}, {}, {})'.format(color.red, color.green,
                                                color.blue, color.alpha)

    def line_cap(self, value):
        if value == 'butt':
            join = 'NVG_BUTT'
        elif (value == 'round'):
            join = 'NVG_ROUND'
        elif (value == 'square'):
            join = 'NVG_SQUARE'
        else:
            print(' !! Not supported value for nvgLineCap():', value)

        self.__append_stmt('LineCap', join)

    def line_to(self, x, y):
        self.__append_stmt('LineTo', x, y)

    def line_join(self, value):
        if value == 'bevel':
            join = 'NVG_BEVEL'
        elif (value == 'miter'):
            join = 'NVG_MITER'
        elif (value == 'round'):
            join = 'NVG_ROUND'
        else:
            print(' !! Not supported value for nvgLineJoin():', value)

        self.__append_stmt('LineJoin', join)

    def linear_gradient(self, sx, sy, ex, ey, scolor, ecolor):
        paint = 'NVGpaint paint = {}'.format(
            self.__gen_stmt('LinearGradient', sx, sy, ex, ey, scolor, ecolor))
        self.stmts.append(paint)
        self.__append_stmt('FillPaint', 'paint')
        self.fill()

    def miter_limit(self, limit):
        self.__append_stmt('MiterLimit', limit)

    def move_to(self, x, y):
        self.__append_stmt('MoveTo', x, y)

    def path_winding_hole(self):
        self.__append_stmt('PathWinding', 'NVG_HOLE')

    def path_winding_solid(self):
        self.__append_stmt('PathWinding', 'NVG_SOLID')

    def quad_to(self, cx, cy, x, y):
        self.__append_stmt('QuadTo', cx, cy, x, y)

    def rect(self, x, y, width, height):
        self.__append_stmt('Rect', x, y, width, height)

    def restore(self):
        self.__append_stmt('Restore')

    def save(self):
        self.__append_stmt('Save')

    def stroke(self):
        self.__append_stmt('Stroke')

    def stroke_color(self, red, green, blue, alpha):
        self.__append_stmt('StrokeColor',
                           self.get_color(red, green, blue, alpha))

    def stroke_color(self, color):
        color = self.get_color_by_object(color)
        self.__append_stmt('StrokeColor', color)

    def stroke_width(self, width):
        self.__append_stmt('StrokeWidth', width)

    def transform(self, a, b, c, d, e, f):
        self.__append_stmt('Transform', a, b, c, d, e, f)
