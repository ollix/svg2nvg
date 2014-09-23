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
parser.add_argument('-c', '--context', default='context',
                    help='the variable name of nanovg context')
parser.add_argument('-d', '--dest', help='the directory for generated file')
parser.add_argument('--header_file', action='store_true',
                    help='generate header file')
parser.add_argument('-ns', '--namespace', action='store_true',
                    help='add C++ namespace to header file')

def execute_from_command_line():
    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()
    svg_parser = SVGParser(args.context)
    svg_parser.parse_file(args.svg_path)
    if args.header_file:
        result = svg_parser.get_header_file_content(args.svg_path,
                                                    args.namespace)
    else:
        result = svg_parser.get_content()
    print(result)

    # Saves the result to a file with the same filename in the destination
    # directory.
    if args.dest is not None:
        filename = '%s.h' % os.path.splitext(os.path.basename(args.svg_path))[0]
        path = os.path.join(os.path.abspath(args.dest), filename)
        f = open(path, 'w')
        f.write(result)
        f.close()
