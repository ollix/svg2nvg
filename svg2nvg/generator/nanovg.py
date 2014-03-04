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
        color = tuple(ord(c) for c in color[1:].decode('hex'))
        opacity = round(float(opacity) * 255)
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

    def fill(self, **kwargs):
        color = self.__gen_color(kwargs['fill'], kwargs['fill_opacity'])
        self._append_stmt('FillColor', color)
        self._append_stmt('Fill')

    def rect(self, **kwargs):
        stmt = self._gen_stmt('Rect', kwargs['x'], kwargs['y'],
                               kwargs['width'], kwargs['height'])
        self._insert_stmt('BeginPath', stmt)

    def stroke(self, **kwargs):
        color = self.__gen_color(kwargs['stroke'], kwargs['stroke_opacity'])
        self._append_stmt('StrokeColor', color)
        self._append_stmt('Stroke')
