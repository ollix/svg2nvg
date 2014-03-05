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


path_commands = (('A', 7), ('C', 6), ('H', 1), ('L', 2), ('M', 2), ('Q', 4),
                 ('S', 4), ('T', 2), ('V', 1), ('Z', 0))

def attr(method):
    def inner(*args, **kwargs):
        self = args[0]
        result = method(*args, **kwargs)
        if result:
            func = getattr(self.generator, method.__name__.rsplit('_')[-1])
            func(**result)
        return result
    return inner

def draw(method):
    def inner(*args, **kwargs):
        self = args[0]
        self.generator.begin_element()
        method(*args, **kwargs)
        self.generator.end_element()
    return inner


class SVGParser(object):

    def __init__(self, generator):
        self.generator = generator

    @draw
    def __convert_rect(self, element):
        args = dict()
        args.update(self.__get_bounds(element))
        args.update(self.__get_fill(element))
        args.update(self.__get_stroke(element))
        self.generator.rect(**args)

    @draw
    def __convert_path(self, element):
        args = dict()

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
                    print("Path command %r should take %d parameters instead of "
                          "%d" % (command, parameter_count, len(parameters)))
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

        args.update(self.__get_fill(element))
        args.update(self.__get_stroke(element))

    @attr
    def __get_bounds(self, element):
        args = dict()
        args['x'] = element.attrib.get('x', 0)
        args['y'] = element.attrib.get('y', 0)
        args['width'] = element.attrib.get('width', 0)
        args['height'] = element.attrib.get('height', 0)
        return args

    @attr
    def __get_fill(self, element):
        args = dict()
        if 'fill' not in element.attrib:
            return args
        fill = element.attrib['fill']
        if fill == 'none' or fill == 'transparent':
            return args
        args['fill'] = fill
        args['fill-opacity'] = element.attrib.get('fill-opacity', 1)
        return args

    @attr
    def __get_stroke(self, element):
        args = dict()
        if 'stroke' not in element.attrib:
            return dict()
        stroke = element.attrib['stroke']
        if stroke == 'none' or stroke == 'transparent':
            return dict()
        args['stroke'] = stroke
        args['stroke-opacity'] = element.attrib.get('stroke-opacity', 1)
        if 'stroke-width' in element.attrib:
            args['stroke-width'] = element.attrib['stroke-width']
            if float(args['stroke-width']) < 1:
                return dict()
        return args

    def __get_tag(self, element):
        return element.tag.rsplit('}')[1]

    def __parse_element(self, element):
        tag = self.__get_tag(element)

        try:
            func = getattr(self,
                           '_' + self.__class__.__name__ + '__convert_%s' % tag)
        except exceptions.AttributeError:
            print('%r element is not supported' % tag)
            exit(1)
        else:
            func(element)

    def __parse_tree(self, tree):
        root = tree.getroot()
        root_tag = self.__get_tag(root)
        if root_tag != 'svg':
            print("The root tag must be svg instead of %r" % root_tag)
            exit(1)

        self.generator.begin()
        self.canvas_width = root.attrib['width']
        self.canvas_height = root.attrib['height']

        for child in root:
            self.__parse_element(child)

        self.generator.end()

    def parse_file(self, filename):
        try:
            tree = ET.parse(filename)
        except exceptions.IOError:
            print('Cannot open SVG file at path: %s' % filename)
        else:
            self.__parse_tree(tree)

    def parse_string(self, string):
        tree = ET.fromstring(string)
        self.__parse_tree(tree)
