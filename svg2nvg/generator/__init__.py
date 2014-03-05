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


class Generator(object):

    def __init__(self):
        self.stmts = list()

    def _append_stmt(self, *args):
        stmt = self._gen_stmt(*args)
        self.stmts.append(stmt)

    def _gen_stmt(self, *args):
        return ''

    def _insert_stmt(self, keyword, stmt):
        index = 0
        for history_stmt in reversed(self.stmts):
            if keyword in history_stmt:
                break
            index -= 1
        index = len(self.stmts) + index
        self.stmts.insert(index, stmt)

    def begin(self):
        pass

    def begin_element(self):
        pass

    def bounds(self, **kwargs):
        pass

    def end(self):
        pass
        print("\n".join(self.stmts))

    def end_element(self):
        pass

    def fill(self, **kwargs):
        pass

    def path_command(self, command, *args):
        pass

    def rect(self, **kwargs):
        pass

    def stroke(self, **kwargs):
        pass
