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

import argparse
import os
import sys

from svg2nvg.parser import SVGParser


parser = argparse.ArgumentParser(
    description='Convert SVG files to NVG source code')
parser.add_argument('svg_path', help='path to a SVG file')
parser.add_argument('-o', '--build_object', action='store_true',
                    help='generate class source files')
parser.add_argument('-c', '--context', default='context',
                    help='the variable name of nanovg context')
parser.add_argument('-d', '--dest', default=os.curdir,
                    help='the directory to keep generated files')
parser.add_argument('--header_file', action='store_true',
                    help='generate header file')
parser.add_argument('-i', '--include_path', default='',
                    help='the include path for generated headers')
parser.add_argument('-vg', '--nanovg_include_path', default='nanovg.h',
                    help='the include path for nanovg')
parser.add_argument('--source_file', action='store_true',
                    help='generate source file')
parser.add_argument('-ns', '--namespace', default='',
                    help='add C++ namespace to header file')
parser.add_argument('-bc', '--baseclass', default='',
                    help='the C++ base class to inherit from')

def execute_from_command_line():
    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()
    svg_parser = SVGParser(args.context)
    svg_parser.parse(args.svg_path)

    basename = os.path.splitext(os.path.basename(args.svg_path))[0]
    dest_path = os.path.join(os.path.abspath(args.dest), basename)

    namespaces = list()
    if args.source_file:
        result = svg_parser.get_header_file_content(basename,
                                                    args.nanovg_include_path,
                                                    args.namespace,
                                                    args.baseclass,
                                                    args.build_object,
                                                    prototype_only=True)
        if args.dest is not None:
            header_file = open('%s.h' % dest_path, 'w')
            header_file.write(result)
            header_file.close()

        result = svg_parser.get_source_file_content(basename,
                                                    args.nanovg_include_path,
                                                    args.namespace,
                                                    args.include_path,
                                                    args.build_object)
        if args.dest is not None:
            source_file = open('%s.cc' % dest_path, 'w')
            source_file.write(result)
            source_file.close()
    elif args.header_file:
        result = svg_parser.get_header_file_content(args.svg_path,
                                                    args.nanovg_include_path,
                                                    args.namespace,
                                                    args.baseclass,
                                                    args.build_object,
                                                    prototype_only=False)
        if args.dest is not None:
            header_file = open('%s.h' % dest_path, 'w')
            header_file.write(result)
            header_file.close()
    else:
        result = svg_parser.get_content()
        print(result)
