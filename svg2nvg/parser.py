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

import os
import re

import svgelements
from svg2nvg import definitions
from svg2nvg import generator


def element(method):
    """Decorator for parsing a element.

    This decorator simply wraps the method between generator's begin_path() and
    end_path() calls with the tag name as the parameter.
    """
    def inner(*args, **kwargs):
        self = args[0]
        element = args[1]
        element.properties = self.get_properties(element)
        if self.begin_element(element):
            method(*args, **kwargs)
            self.end_element(element)
    return inner


class SVGParser(object):

    def __init__(self, context='context'):
        self.context = context
        self.groups = list()
        self.linear_gradients = dict()
        self.stmts = list()
        self.properties = list()
        self.path_began = False

    def __begin_path(self, element):
        if self.path_began is True and \
           self.__check_property_changed(element, 'fill', 'stroke'):
            self.generator.begin_path()
        elif self.path_began is False:
            self.path_began = True
            self.generator.begin_path()

    def __end_path(self, element):
        self.__process_properties(element, 'stroke_width', 'stroke')

        try:
            fill_id_match = re.match(r'url\(#(.*)\)', element.values['fill'])
            fill_id = fill_id_match.group(1)
            gradient = self.linear_gradients[fill_id]
        except:
            self.__process_property(element, 'fill')
        else:
            self.__fill_linear_gradient(element, gradient)

        while element.save_count > 0:
            self.__restore(element)

    def __fill_linear_gradient(self, element, gradient):
        if not gradient.stops:
            self.__process_property(element, 'fill')
            return

        keys = list(gradient.stops.keys())
        keys.sort()
        first_offset = keys[0]
        last_offset = keys[1]

        first_color = gradient.stops[first_offset]
        last_color = gradient.stops[last_offset]

        if first_color == last_color:
            element.properties['fill'] = first_color
            self.__process_property(element, 'fill')
            return

        values = gradient.values
        x1 = float(values['x1'])
        y1 = float(values['y1'])
        x2 = float(values['x2'])
        y2 = float(values['y2'])

        sx = x1 + (x2 - x1) * first_offset
        sy = y1 + (y2 - y1) * first_offset
        ex = x1 + (x2 - x1) * last_offset
        ey = y1 + (y2 - y1) * last_offset

        get_color = self.generator.get_color_by_object
        self.generator.linear_gradient(sx, sy, ex, ey,
                                       get_color(first_color),
                                       get_color(last_color))
        self.path_began = False

    @element
    def __parse_circle(self, element):
        self.generator.circle(element.cx, element.cy, element.rx)

    @element
    def __parse_ellipse(self, element):
        self.generator.ellipse(element.cx, element.cy, element.rx, element.ry)

    @element
    def __parse_group(self, group):
        for child in group:
            try:
                if child.values['visibility'] == 'hidden':
                    continue
            except (KeyError, AttributeError):
                pass

            if isinstance(child, svgelements.Circle):
                self.__parse_circle(child)
            elif isinstance(child, svgelements.Ellipse):
                self.__parse_ellipse(child)
            elif isinstance(child, svgelements.Group):
                self.__parse_group(child)
            elif isinstance(child, svgelements.Path):
                self.__parse_path(child)
            elif isinstance(child, svgelements.Polygon):
                self.__parse_polygon(child)
            elif isinstance(child, svgelements.Polyline):
                self.__parse_polyline(child)
            elif isinstance(child, svgelements.Rect):
                self.__parse_rect(child)
            elif isinstance(child, svgelements.SimpleLine):
                self.__parse_line(child)
            elif isinstance(child, svgelements.SVGElement):
                self.__parse_other_element(child)
            elif isinstance(child, svgelements.Shape):
                print(" !! Unsupported shape:", element.__class__)

        while group.save_count > 0:
            self.__restore(group)

    @element
    def __parse_line(self, element):
        self.generator.move_to(element.x1, element.y1)
        self.generator.line_to(element.x2, element.y2)

    def __parse_linear_gradient(self, element):
        self.linear_gradients[element.id] = element
        element.stops = dict()

    def __parse_other_element(self, element):
        tag = element.values['tag']
        if tag == 'linearGradient':
            self.__parse_linear_gradient(element)
        elif tag == 'stop':
            self.__parse_stop(element)

    @element
    def __parse_path(self, element):
        subpath_count = 0
        for segment in element:
            if (isinstance(segment, svgelements.svgelements.Arc)):
                pass
            elif (isinstance(segment, svgelements.svgelements.Close)):
                self.generator.close_path()
                if subpath_count > 1:
                    self.generator.path_winding_hole()
            elif (isinstance(segment, svgelements.svgelements.CubicBezier)):
                control1 = segment.control1
                control2 = segment.control2
                point = segment.end
                self.generator.bezier_to(control1.x, control1.y,
                                         control2.x, control2.y,
                                         point.x, point.y)
            elif (isinstance(segment, svgelements.svgelements.Line)):
                point = segment.end
                self.generator.line_to(point.x, point.y)
            elif (isinstance(segment, svgelements.svgelements.Move)):
                subpath_count += 1
                point = segment.end
                self.generator.move_to(point.x, point.y)
            elif (isinstance(segment, svgelements.svgelements.QuadraticBezier)):
                control = segment.control
                point = segment.end
                self.generator.bezier_to(control1.x, control1.y,
                                         control2.x, control2.y,
                                         point.x, point.y)
            else:
                print(segment.__class__)

    @element
    def __parse_polygon(self, element):
        if len(element) < 3:
            return

        first_point = element.points[0]
        for point in element.points:
            if point == first_point:
                self.generator.move_to(point.x, point.y)
            else:
                self.generator.line_to(point.x, point.y)

        if point != first_point:
            self.generator.close_path()

    @element
    def __parse_polyline(self, element):
        if len(element) < 2:
            return

        first_point = element.points[0]
        for point in element.points:
            if point == first_point:
                self.generator.move_to(point.x, point.y)
            else:
                self.generator.line_to(point.x, point.y)

    @element
    def __parse_rect(self, element):
        self.generator.rect(element.x, element.y, element.width, element.height)

    def __parse_stop(self, element):
        if not self.linear_gradients:
            return

        stop_color = svgelements.svgelements.Color(element.values['stop-color'])
        gradient = self.linear_gradients[list(self.linear_gradients)[-1]]
        gradient.stops[float(element.values['offset'])] = stop_color

    def __check_property_changed(self, element, *property_names):
        for property_name in property_names:
            try:
                expected_value = element.properties[property_name]
            except KeyError:
                continue

            if property_name == 'transform' and len(expected_value) != 6:
                continue

            current_value = self.__get_current_property_value(property_name)

            if property_name == 'transform':
                for i in range(6):
                    if expected_value[i] != current_value[i]:
                        return True
                continue

            if (expected_value != current_value):
                return True

        return False

    def __get_current_property_value(self, property_name):
        for properties in reversed(self.properties):
            if property_name in properties:
                return properties[property_name]
        return None

    def __process_property(self, element, property_name):
        """Updates a current property with an element's property.

        Returns `True` if the property did udpate.
        """
        try:
            expected_value = element.properties[property_name]
        except KeyError:
            return

        value_changed = self.__check_property_changed(element, property_name)
        if isinstance(expected_value, svgelements.svgelements.Color):
            if value_changed or expected_value.opacity:
                self.path_began = False
        elif not value_changed:
            return

        if property_name == 'fill':
            if value_changed:
                self.generator.fill_color(expected_value)
            if expected_value.opacity:
                self.generator.fill()
        elif property_name == 'linecap':
            self.generator.line_cap(expected_value)
        elif property_name == 'linejoin':
            self.generator.line_join(expected_value)
        elif property_name == 'miterlimit':
            self.generator.miter_limit(expected_value)
        elif property_name == 'stroke':
            if value_changed:
                self.generator.stroke_color(expected_value)
            if expected_value.opacity:
                self.generator.stroke()
        elif property_name == 'stroke_width':
            self.generator.stroke_width(expected_value)
        elif property_name == 'transform':
            self.__save(element)
            self.generator.transform(expected_value[0], expected_value[1],
                                     expected_value[2], expected_value[3],
                                     expected_value[4], expected_value[5])

        self.properties[-1][property_name] = expected_value

    def __process_properties(self, element, *property_names):
        for property_name in property_names:
            self.__process_property(element, property_name)

    def __restore(self, element):
        element.save_count -= 1
        self.properties.pop()
        self.generator.restore()

    def __save(self, element):
        element.save_count += 1
        self.properties.append(dict())
        self.generator.save()

    def begin_element(self, element):
        element.is_path = isinstance(element, svgelements.Shape)
        element.is_group = isinstance(element, svgelements.Group)
        element.save_count = 0

        if element.is_group and len(element) == 0:
            return False

        self.__process_properties(element, 'linecap', 'linejoin', 'miterlimit',
                                  'transform')

        if element.is_path:
            self.__begin_path(element)

        self.last_element = element
        return True

    def end_element(self, element):
        if element.is_path:
            self.__end_path(element)

    def get_content(self):
        return '\n'.join(self.stmts)

    def get_properties(self, element):
        properties = dict()
        values = element.values

        if 'stroke-linecap' in values:
            properties['linecap'] = values['stroke-linecap']

        if 'stroke-linejoin' in values:
            properties['linejoin'] = values['stroke-linejoin']

        if 'stroke-miterlimit' in values:
            properties['miterlimit'] = values['stroke-miterlimit']

        properties['transform'] = element.transform

        if isinstance(element, svgelements.Shape):
            properties['fill'] = element.fill
            properties['stroke_width'] = element.stroke_width
            properties['stroke'] = element.stroke

        return properties

    def get_header_file_content(self, filename, nanovg_include_path,
                                namespace='', baseclass='',
                                builds_object=False, prototype_only=False):
        basename = os.path.splitext(os.path.basename(filename))[0]
        guard_constant = 'SVG2NVG_%s_H_' % basename.upper()
        title = basename.title().replace('_', '')

        result = '#ifndef %s\n' % guard_constant
        result += '#define %s\n\n' % guard_constant

        if nanovg_include_path:
            result += '#include "%s"\n\n' % nanovg_include_path

        if namespace:
            result += 'namespace %s {\n\n' % namespace

        if builds_object:
            function_name = 'Draw'
            inheritance = ' : public %s' % baseclass if baseclass else ''
            result += 'class %s%s {\n' % (title, inheritance)
            result += ' public:\n'
            result += '  double GetWidth() const final { return %s; }\n' % \
                      self.canvas_width
            result += '  double GetHeight() const final { return %s; }\n\n' % \
                      self.canvas_height
        else:
            function_name = 'Render%s' % title

        prototype = '  void %s(NVGcontext *%s) const final' % \
                    (function_name, self.context)
        if prototype_only:
            result += '%s;\n' % prototype
        else:
            result += 'static %s {\n' % prototype
            for stmt in self.stmts:
                result += '  %s\n' % stmt
            result += '}\n'

        if builds_object:
            result += '};\n'

        result += '\n'
        if namespace:
            result += '}  // namespace %s\n\n' % namespace
        result += '#endif  // %s\n' % guard_constant
        return result

    def get_source_file_content(self, filename, nanovg_include_path,
                                namespace='',
                                header_include_path=None,
                                builds_object=False):
        result = ''
        basename = os.path.splitext(os.path.basename(filename))[0]
        if header_include_path is None:
            header_include_path = ''
        header_name = '%s.h' % basename
        header_include_path = os.path.join(header_include_path, header_name)
        result += '#include "%s"\n\n' % header_include_path

        if nanovg_include_path:
            result += '#include "%s"\n\n' % nanovg_include_path

        if namespace:
            result += 'namespace %s {\n\n' % namespace

        title = basename.title().replace('_', '')
        result += 'void '
        if builds_object:
            function_name = 'Draw'
            result += '%s::' % title
        else:
            function_name = 'Render%s' % title
        result += '%s(NVGcontext *%s) const {\n' % (function_name, self.context)
        for stmt in self.stmts:
            result += '  %s\n' % stmt
        result += '}\n\n'
        if namespace:
            result += '}  // namespace %s\n' % namespace
        return result

    def parse(self, source):
        svg = svgelements.SVG.parse(source, color=None)
        self.groups.clear()
        self.linear_gradients.clear()
        self.properties.clear()
        self.properties.append(dict(transform=[1, 0, 0, 1, 0, 0]))
        self.canvas_width = svg.width
        self.canvas_height = svg.height
        self.generator = generator.Generator(self.stmts, self.context)
        self.last_element = None

        self.__parse_group(svg)

        if self.path_began:
            element = self.last_element
            if element.fill.opacity:
                self.generator.fill()
            if element.stroke.opacity:
                self.generator.stroke()
