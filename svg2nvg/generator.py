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

class Generator(object):

    def __init__(self, stmts, context='context'):
        self.context = context
        self.stmts = stmts

    def __append_stmt(self, *args):
        stmt = self.__gen_stmt(*args)
        self.stmts.append(stmt)

    def __gen_color(self, color, opacity):
        if color == 'none' or not color or opacity == 0:
            return None

        opacity = round(float(opacity) * 255)
        if color.startswith('#'):
            color = color[1:]
            if len(color) == 3:
                color = ''.join([c + c for c in color])
            color = tuple(ord(c) for c in color.decode('hex'))
        elif color == 'black':
            color = (255, 255, 255)
        return 'nvgRGBA(%d, %d, %d, %d)' % (color[0], color[1], color[2],
                                            opacity)

    def __gen_stmt(self, *args):
        command = args[0]
        if len(args) == 1:
            stmt = 'nvg%s(%s);' % (command, self.context)
        else:
            args = tuple(str(arg) for arg in args[1:])
            stmt = 'nvg%s(%s, %s);' % (command, self.context, ', '.join(args))
        return stmt

    def __insert_stmt(self, keyword, stmt):
        index = 0
        for history_stmt in reversed(self.stmts):
            if keyword in history_stmt:
                break
            index -= 1
        index = len(self.stmts) + index
        self.stmts.insert(index, stmt)

    def begin_element(self, tag):
        if tag not in ('g',):
            self.__append_stmt('BeginPath')
        self.previous_path_xy = (0, 0)

    def begin_path_commands(self):
        self.subpath_count = 0
        self.previous_path = None
        self.previous_move_point = None

    def bounds(self, **kwargs):
        pass

    def circle(self, **kwargs):
        stmt = self.__gen_stmt('Circle', kwargs['cx'], kwargs['cy'],
                               kwargs['r'])
        self.__insert_stmt('BeginPath', stmt)

    def ellipse(self, **kwargs):
        stmt = self.__gen_stmt('Ellipse', kwargs['cx'], kwargs['cy'],
                               kwargs['rx'], kwargs['ry'])
        self.__insert_stmt('BeginPath', stmt)

    def end_element(self, tag):
        pass

    def end_path_commands(self):
        self.previous_path = None

    def fill(self, **kwargs):
        color = self.__gen_color(kwargs['fill'], kwargs['fill-opacity'])
        if color is not None:
            self.__append_stmt('FillColor', color)
        self.__append_stmt('Fill')

    def line(self, x1, y1, x2, y2):
        self.__append_stmt('MoveTo', x1, y1);
        self.__append_stmt('LineTo', x2, y2);

    def path_command(self, command, *args):
        # Converts relative coordinates to absolute coordinates.
        if command.islower():
            previous_x = float(self.previous_path_xy[0])
            previous_y = float(self.previous_path_xy[1])

            if command in ('c', 'h', 'l', 'm', 's', 'q'):
                new_args = list()
                for i, value in enumerate(args):
                    previous_value = float(self.previous_path_xy[i % 2])
                    new_args.append(float(args[i]) + previous_value)
                args = tuple(new_args)
            elif command == 'v':
                args = (previous_y + float(args[0]),)
            elif command == 'z':
                pass
            else:
                print("Path command %r is not implmeneted" % command)
                exit(1)
            command = command.upper()

        # Converts 'H', 'S' and 'V' commands to other generic commands.
        if command == 'H':
            command = 'L'
            args = (args[0], self.previous_path_xy[1])
        elif command == 'S':
            if self.previous_path is None:
                previous_command = None
            else:
                previous_command = self.previous_path[0]
                previous_parameters = self.previous_path[1]

            if previous_command == 'C':
                previous_x = float(previous_parameters[4])
                previous_y = float(previous_parameters[5])
                previous_x2 = float(previous_parameters[2])
                previous_y2 = float(previous_parameters[3])
                x1 = 2 * previous_x - previous_x2
                y1 = 2 * previous_y - previous_y2
                command = 'C'
                args = (x1, y1) + args
            else:
                print('Path command S is not implement')
        elif command == 'V':
            command = 'L'
            args = (self.previous_path_xy[0], args[0])

        # Moves to the previous move point if the previous command is closepath.
        if self.previous_path is not None and \
           self.previous_move_point is not None and \
           self.previous_path[0] == 'Z' and command != 'M':
            self.subpath_count += 1
            self.__append_stmt('MoveTo', self.previous_move_point)

        # Handles generic commands.
        if command == 'C':
            self.__append_stmt('BezierTo', *args)
            self.previous_path_xy = args[-2:]
        elif command == 'L':
            self.__append_stmt('LineTo', *args)
            self.previous_path_xy = args
        elif command == 'M':
            self.subpath_count += 1
            self.__append_stmt('MoveTo', *args)
            self.previous_path_xy = args
            self.previous_move_point = args
        elif command == 'Q':
            self.__append_stmt('QuadTo', *args)
            self.previous_path_xy = args[-2:]
        elif command == 'Z':
            self.__append_stmt('ClosePath')
            if self.subpath_count > 1:
                self.__append_stmt('PathWinding', 'NVG_HOLE')
        else:
            print('Path command %r is not implemented: %r' % (command, args))
            exit(1)
        self.previous_path = (command, args)

    def polygon(self, **kwargs):
        points = [tuple(point.split(',')) for point in kwargs['points'].split()]
        self.__append_stmt('MoveTo', *points[0])
        for point in points[1:]:
            self.__append_stmt('LineTo', *point)
        self.__append_stmt('ClosePath')

    def rect(self, **kwargs):
        stmt = self.__gen_stmt('Rect', kwargs['x'], kwargs['y'],
                               kwargs['width'], kwargs['height'])
        self.__insert_stmt('BeginPath', stmt)

    def stroke(self, **kwargs):
        color = self.__gen_color(kwargs['stroke'], kwargs['stroke-opacity'])
        if color is not None:
            self.__append_stmt('StrokeColor', color)

        if 'stroke-linecap' in kwargs:
            line_caps = {'butt': 'NVG_BUTT', 'round': 'NVG_ROUND',
                         'square': 'NVG_SQUARE'}
            line_cap = kwargs['stroke-linecap']
            if line_cap in line_caps:
              self.__append_stmt('LineCap', line_caps[line_cap])

        if 'stroke-width' in kwargs:
            self.__append_stmt('StrokeWidth', kwargs['stroke-width'])
        self.__append_stmt('Stroke')
