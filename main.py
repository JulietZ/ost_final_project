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
    modifyDate = ndb.DateTimeProperty(auto_now=True)
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

        questions_query = Questions.query().order(-Questions.createDate)
        questions = questions_query.fetch(10)
        #questions = ndb.gql("Select * from Questions Order by createDate desc")
        template_values = {
            'user': users.get_current_user(),
            'questions': questions,
            'url': url
        }
        template = JINJA_ENVIRONMENT.get_template('mainpage.html')
        self.response.write(template.render(template_values))

class CreateQuestion(webapp2.RequestHandler):
    def post(self):
        if self.request.get('equestion'):
            questionKey=self.request.get('equestion')
            question=ndb.Key(urlsafe = questionKey).get()
            question.title=self.request.get('eqtitle')
            question.content=self.request.get('eqcontent')
            question.tag=self.request.get('eqtag',allow_multiple=True)
            question.put()
            self.redirect('/')

        elif self.request.get('qtitle'):
            question=Questions()
            if users.get_current_user():
                question.author = users.get_current_user()
                question.title = self.request.get('qtitle')
                question.content = self.request.get('qcontent')
                question.voteScore = 0
                question.tag = self.request.get('qtag', allow_multiple=True)
                question.put()
                self.redirect('/')

            else:
                self.redirect(users.create_login_url(self.request.uri))

class Personal(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        question_qry = Questions.query(Questions.author == user).order(-Questions.createDate)
        questions=question_qry.fetch(10)
        template_values = {
            'user': user,
            'questions': questions
        }
        template = JINJA_ENVIRONMENT.get_template('homepage.html')
        self.response.write(template.render(template_values))        

class EditQuestion(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if self.request.get('questionKey'):
            questionKey=self.request.get('questionKey')
            question=ndb.Key(urlsafe = questionKey).get()
            template_values = {
                'user': user,
                'question': question
            }
            template = JINJA_ENVIRONMENT.get_template('edit.html')
            self.response.write(template.render(template_values))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/question', CreateQuestion),
    ('/personal', Personal),
    ('/edit', EditQuestion),
], debug=True)

