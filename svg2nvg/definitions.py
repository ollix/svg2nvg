# Copyright (c) 2016 Olli Wang. All right reserved.
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

import functools
import re
import sys


class Definition(object):

    def generate_stmts(self):
        pass

class LinearGradientDefinition(Definition):

    def __init__(self, element):
        x1 = float(element.attrib['x1'])
        y1 = float(element.attrib['y1'])
        x2 = float(element.attrib['x2'])
        y2 = float(element.attrib['y2'])

        # Determines the transform.
        self.transform = None
        transform = element.attrib.get('gradientTransform', None);
        self.should_restore = False
        if transform:
            match = re.match(r'matrix\((.*)\)', transform)
            if match:
                transform = match.group(1).split()
                if (len(transform) == 6):
                    self.transform = transform
                    self.should_restore = True

        self.stops = []
        for stop in element:
            if stop.tag.rsplit('}')[1] != 'stop':
                continue

            # Determines the color.
            style = stop.get('style')
            color_match = re.match(r'.*stop-color:#([0-9a-fA-F]{6})', style)
            if not color_match:
                continue
            color = color_match.group(1)

            # Determines the opacity.
            opacity_match = re.match(r'.*stop-opacity:([-+]?[0-9]*\.?[0-9]+)',
                                     style)
            if opacity_match:
                opacity = float(opacity_match.group(1)) * 255
            else:
                opacity = 255

            if sys.version_info[0] < 3:
                color = tuple(ord(c) for c in color.decode('hex'))
            else:
                color = tuple(c for c in bytes.fromhex(color))
            color = 'nvgRGBA(%d, %d, %d, %d)' % (color[0], color[1], color[2],
                                                 opacity)

            # Determines the coordinate x and y
            offset = float(stop.attrib['offset'])
            m = offset
            n =  1- m
            x = (m * x2 + n * x1) / (m + n)
            y = (m * y2 + n * y1) / (m + n)

            self.stops.append({'offset': offset, 'color': color,
                               'x': x, 'y': y})
        self.stops = sorted(self.stops, key=(lambda x: x['offset']))

        if len(self.stops) > 2:
            print("<linearGradient> currently only supports two stops.")
            exit(1)

    def generate_stmts(self):
        stmts = []
        src_stop = None

        if self.transform is not None:
            stmts.append(['Save'])
            stmts.append(['Transform'] + self.transform)

        for dest_stop in self.stops:
            if src_stop is None:
                src_stop = dest_stop
                continue

            stmts.append(['LinearGradient', src_stop['x'], src_stop['y'],
                          dest_stop['x'], dest_stop['y'], src_stop['color'],
                          dest_stop['color']])
            stmts.append(['FillPaint'])
            src_stop = dest_stop
        return stmts
