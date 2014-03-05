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

from svg2nvg import generator


class NanoVGGenerator(generator.Generator):

    def __init__(self, context='context'):
        super(NanoVGGenerator, self).__init__()
        self.context = context

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

    def _gen_stmt(self, *args):
        command = args[0]
        if len(args) == 1:
            stmt = 'nvg%s(%s);' % (command, self.context)
        else:
            args = tuple(str(arg) for arg in args[1:])
            stmt = 'nvg%s(%s, %s);' % (command, self.context, ', '.join(args))
        return stmt

    def begin_element(self):
        self._append_stmt('BeginPath')
        self.previous_path_xy = (0, 0)
        self.previous_path = None

    def fill(self, **kwargs):
        color = self.__gen_color(kwargs['fill'], kwargs['fill-opacity'])
        if color is not None:
            self._append_stmt('FillColor', color)
        self._append_stmt('Fill')

    def path_command(self, command, *args):
        # Converts relative coordinate to absolute coordinate.
        if command.lower() == command:
            previous_x = float(self.previous_path_xy[0])
            previous_y = float(self.previous_path_xy[1])
            if command == 'c':
                args = (previous_x + float(args[0]),
                        previous_y + float(args[1]),
                        previous_x + float(args[2]),
                        previous_y + float(args[3]),
                        previous_x + float(args[4]),
                        previous_y + float(args[5]))
            elif command == 'h':
                args = (previous_x + float(args[0]),)
            elif command == 'm':
                args = (previous_x + float(args[0]),
                        previous_y + float(args[1]))
            elif command == 's':
                args = (previous_x + float(args[0]),
                        previous_y + float(args[1]),
                        previous_x + float(args[2]),
                        previous_y + float(args[3]))
            elif command == 'v':
                args = (previous_y + float(args[0]),)
            elif command == 'z':
                pass
            else:
                print("Path command %r is not implmeneted" % command)
                exit(1)
            command = command.upper()

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

        if command == 'C':
            self._append_stmt('BezierTo', *args)
            self.previous_path_xy = args[-2:]
        elif command == 'L':
            self._append_stmt('LineTo', *args)
            self.previous_path_xy = args
        elif command == 'M':
            self._append_stmt('MoveTo', *args)
            self.previous_path_xy = args
        elif command == 'Z':
            self._append_stmt('ClosePath')
        else:
            print('Path command %r is not implemented: %r' % (command, args))
            exit(1)
        self.previous_path = (command, args)

    def rect(self, **kwargs):
        stmt = self._gen_stmt('Rect', kwargs['x'], kwargs['y'],
                               kwargs['width'], kwargs['height'])
        self._insert_stmt('BeginPath', stmt)

    def stroke(self, **kwargs):
        color = self.__gen_color(kwargs['stroke'], kwargs['stroke-opacity'])
        if color is not None:
            self._append_stmt('StrokeColor', color)
        if 'stroke-width' in kwargs:
            self._append_stmt('StrokeWidth', kwargs['stroke-width'])
        self._append_stmt('Stroke')
