#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#

from google.appengine.api import users
from google.appengine.ext import db
import webapp2

class Question(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        self.response.out.write('<html><body>')
        self.response.out.write('%s' % user.nickname())
        self.response.out.write('</html></body>')


app = webapp2.WSGIApplication([
    ('/question', Question)
], debug=True)
