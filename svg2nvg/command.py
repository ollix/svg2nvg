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
import sys

from svg2nvg.parser import SVGParser
from svg2nvg.generator import nanovg


def convert_svg_file_to_nvg(filename):
    generator = nanovg.NanoVGGenerator()
    parser = SVGParser(generator)
    parser.parse_file(filename)


parser = argparse.ArgumentParser(
    description='Convert SVG files to NVG source code')
parser.add_argument('svg_path', help='path to a SVG file')

def execute_from_command_line():
    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()
    convert_svg_file_to_nvg(args.svg_path)
