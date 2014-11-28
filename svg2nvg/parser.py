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

import exceptions
import os
import xml.etree.ElementTree as ET

from svg2nvg import generator


# A list of tag names that should be ignored when parsing.
ignored_tags = ('defs',)
# A list of supported path commands and the number of parameters each command
# requires.
path_commands = (('A', 7), ('C', 6), ('H', 1), ('L', 2), ('M', 2), ('Q', 4),
                 ('S', 4), ('T', 2), ('V', 1), ('Z', 0))


def attribute(method):
    """Decorator for parsing element attributes.

    Methods with this decorator must return a dictionary with interested
    attributes. The dictionary will then be passed to corresponded generator
    method as parameters.
    """
    def inner(*args, **kwargs):
        self = args[0]
        result = method(*args, **kwargs)
        if result:
            func = getattr(self.generator, method.__name__.rsplit('_')[-1])
            func(**result)
        return result
    return inner

def element(method):
    """Decorator for parsing a element.

    This decorator simply wraps the method between generator's begin_element()
    and end_element() calls with the tag name as the parameter.
    """
    def inner(*args, **kwargs):
        self = args[0]
        element_tag = get_element_tag(args[1])
        self.generator.begin_element(element_tag)
        method(*args, **kwargs)
        self.generator.end_element(element_tag)
    return inner

def get_element_tag(element):
    """Returns the tag name string without namespace of the passed element."""
    return element.tag.rsplit('}')[1].lower()


class SVGParser(object):

    def __init__(self, context='context'):
        self.context = context
        self.stmts = list()

    @attribute
    def __parse_bounds(self, element):
        args = dict()
        args['x'] = element.attrib.get('x', 0)
        args['y'] = element.attrib.get('y', 0)
        args['width'] = element.attrib.get('width', 0)
        args['height'] = element.attrib.get('height', 0)
        return args

    @element
    def __parse_circle(self, element):
        self.__parse_fill(element)
        self.__parse_stroke(element)
        self.generator.circle(**element.attrib)

    @element
    def __parse_ellipse(self, element):
        self.__parse_fill(element)
        self.__parse_stroke(element)
        self.generator.ellipse(**element.attrib)

    @attribute
    def __parse_fill(self, element):
        args = dict()
        if 'fill' not in element.attrib:
            fill = '#000000'
        else:
            fill = element.attrib['fill']
        if fill == 'none' or fill == 'transparent':
            return args
        args['fill'] = fill
        args['fill-opacity'] = float(element.attrib.get('opacity', 1)) * \
                               float(element.attrib.get('fill-opacity', 1))
        return args

    @element
    def __parse_g(self, element):
        # Gathers all group attributes at current level.
        self.group_attrib.append(element.attrib)
        group_attrib = dict()
        for attrib in self.group_attrib:
            group_attrib.update(attrib)

        # Applies group attributes to child elements.
        for child in element:
            child.attrib.update(group_attrib)
            self.__parse_element(child)

        # Removes the group attributes at current level.
        self.group_attrib.pop()

    @element
    def __parse_line(self, element):
        self.generator.line(element.attrib['x1'], element.attrib['y1'],
                            element.attrib['x2'], element.attrib['y2'])
        self.__parse_fill(element);
        self.__parse_stroke(element);

    @element
    def __parse_rect(self, element):
        self.__parse_bounds(element)
        self.__parse_fill(element)
        self.__parse_stroke(element)
        self.generator.rect(**element.attrib)

    @element
    def __parse_path(self, element):
        def execute_command(command, parameters):
            if not command:
                return
            for path_command in path_commands:
                if path_command[0] == command.upper():
                    break
            else:
                print("Path command %r is not supported." % command)
            parameter_count = path_command[1]

            if parameter_count == 0:
                if parameters:
                    print("Path command %r should not take parameters: %s" % \
                          (command, parameters))
                    exit(1)
                self.generator.path_command(command)
            else:
                # Checks if the number of parameters matched.
                if (len(parameters) % parameter_count) != 0:
                    print("Path command %r should take %d parameters instead "
                          "of %d" % (command, parameter_count, len(parameters)))
                    exit(1)
                while parameters:
                    self.generator.path_command(command,
                                                *parameters[:parameter_count])
                    parameters = parameters[parameter_count:]

        parameters = list()
        command = None
        parameter_string = list()

        commands = tuple(c[0] for c in path_commands) + \
                   tuple(c[0].lower() for c in path_commands)

        self.generator.begin_path_commands()
        for char in element.attrib['d']:
            if char in ['\n', '\t']:
                continue
            elif char in commands:  # found command
                if parameter_string:
                    parameters.append(''.join(parameter_string))
                    parameter_string = list()
                execute_command(command, parameters)
                command = char
                parameters = list()
            elif char in [' ', ',', '-']:
                if parameter_string:
                    parameters.append(''.join(parameter_string))
                    parameter_string = list()
                if char in ['-']:
                    parameter_string.append(char)
            elif command is not None:
                parameter_string.append(char)

        if parameter_string:
            parameters.append(''.join(parameter_string))
            parameter_string = list()
        execute_command(command, parameters)
        self.generator.end_path_commands()

        self.__parse_fill(element)
        self.__parse_stroke(element)

    @element
    def __parse_polygon(self, element):
        self.generator.polygon(**element.attrib)
        self.__parse_fill(element)
        self.__parse_stroke(element)

    @attribute
    def __parse_stroke(self, element):
        args = dict()
        if 'stroke' not in element.attrib:
            return dict()
        stroke = element.attrib['stroke']
        if stroke == 'none' or stroke == 'transparent':
            return dict()
        args['stroke'] = stroke
        args['stroke-opacity'] = float(element.attrib.get('opacity', 1)) * \
                                 float(element.attrib.get('stroke-opacity', 1))

        for attrib in ['linecap', 'linejoin', 'miterlimit']:
            attrib = 'stroke-%s' % attrib
            if attrib in element.attrib:
                args[attrib] = element.attrib[attrib]

        if 'stroke-width' in element.attrib:
            args['stroke-width'] = element.attrib['stroke-width']
            if float(args['stroke-width']) < 1:
                return dict()

        return args

    def __parse_element(self, element):
        tag = get_element_tag(element)
        if tag in ignored_tags:
            return

        # Deteremins the method for parsing the passed element.
        method_name = '_' + self.__class__.__name__ + '__parse_%s' % tag
        try:
            method = getattr(self, method_name)
        except exceptions.AttributeError:
            print('Error: %r element is not supported' % tag)
            exit(1)
        else:
            method(element)

    def __parse_tree(self, tree):
        root = tree.getroot()
        root_tag = get_element_tag(root)
        if root_tag != 'svg':
            print("Error: the root tag must be svg instead of %r" % root_tag)
            exit(1)

        del self.stmts[:]  # clears the cached statements.

        self.canvas_width = root.attrib['width']
        self.canvas_height = root.attrib['height']
        self.generator = generator.Generator(self.stmts, self.context)
        self.group_attrib = list()

        for child in root:
            self.__parse_element(child)

    def get_content(self):
        return '\n'.join(self.stmts)

    def get_header_file_content(self, filename, namespace=False):
        basename = os.path.splitext(os.path.basename(filename))[0]
        guard_constant = 'SVG2NVG_%s_H_' % basename.upper()
        function_name = 'Draw%s' % basename.title().replace('_', '')

        result = '#ifndef %s\n' % guard_constant
        result += '#define %s\n' % guard_constant
        if namespace:
            result += '\nnamespace svg2nvg {\n'
        result += '\nvoid %s(NVGcontext* %s) {\n' % (function_name,
                                                     self.context)
        for stmt in self.stmts:
            result += '  %s\n' % stmt
        result += '}\n\n'
        if namespace:
            result += '}  // namespace svg2nvg\n\n'
        result += '#endif  // %s\n' % guard_constant
        return result

    def parse_file(self, filename):
        try:
            tree = ET.parse(filename)
        except exceptions.IOError:
            print('Error: cannot open SVG file at path: %s' % filename)
            exit(1)
        else:
            self.__parse_tree(tree)

    def parse_string(self, string):
        tree = ET.fromstring(string)
        self.__parse_tree(tree)
