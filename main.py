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

import cgi
import urllib
from google.appengine.api import users
from google.appengine.ext import ndb
import webapp2
import os
import jinja2
import datetime

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def site_key():
    """Constructs a website key for All questions."""
    return ndb.Key('Site', 'site')

class Questions(ndb.Model):
    """Models an individual Question entry """
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    createDate = ndb.DateTimeProperty(auto_now_add=True)
    title = ndb.StringProperty(indexed=False)
    modifyDate = ndb.DateTimeProperty()
    tag = ndb.StringProperty(repeated=True)
    voteScore = ndb.IntegerProperty()
    
class Answers(ndb.Model):
    """Models an individual Answer entry """
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    createDate = ndb.DateTimeProperty(auto_now_add=True)
    modifyDate = ndb.DateTimeProperty()
    voteScore = ndb.IntegerProperty()
    qAuthor = ndb.UserProperty()
    qTitle = ndb.StringProperty(indexed=False)

class Votes(ndb.Model):
    author = ndb.UserProperty(required=True)
    createDate = ndb.DateTimeProperty(auto_now_add=True)
    voteType = ndb.StringProperty(choices=set(["up", "down"]))


class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)

        else:
            url = users.create_login_url(self.request.uri)
        questions_query = Questions.query(
           ancestor=site_key()).order(-Questions.createDate)
        questions = questions_query.fetch(10)
        template_values = {
            'user': users.get_current_user(),
            'questions': questions,
            'url': url
        }
        template = JINJA_ENVIRONMENT.get_template('mainpage.html')
        self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', MainPage)
], debug=True)

