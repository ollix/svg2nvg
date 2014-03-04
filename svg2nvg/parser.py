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


def attr(method):
    def inner(*args, **kwargs):
        self = args[0]
        result = method(*args, **kwargs)
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
        self.generator.rect(**args)

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
        args['fill'] = element.attrib.get('fill', '')
        args['fill_opacity'] = element.attrib.get('fill-opacity', 1)
        return args

    @attr
    def __get_stroke(self, element):
        args = dict()
        args['stroke'] = element.attrib.get('stroke', '')
        args['stroke_opacity'] = element.attrib.get('stroke-opacity', 1)
        return args

    def __get_tag(self, element):
        return element.tag.rsplit('}')[1]

    def __parse_element(self, element):
        tag = self.__get_tag(element)

        try:
            func = getattr(self,
                           '_' + self.__class__.__name__ + '__convert_%s' % tag)
        except exceptions.AttributeError:
            pass
        else:
            func(element)

    def __parse_tree(self, tree):
        root = tree.getroot()
        root_tag = self.__get_tag(root)
        if root_tag != 'svg':
            print("The root tag must be svg instead of %r" % root_tag)
            return

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
