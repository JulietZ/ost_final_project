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
from google.appengine.ext import db
import webapp2

class User(db.Model):
	userid = db.StringProperty(required=True)

class Questions(db.Model):
	questionTime = db.DateProperty(auto_now_add=True)
	questionUser = db.StringProperty(required=True)
	questionName = db.StringProperty(required=True)
	questionContent = db.StringProperty(required=True)
	#questionTag = #list, tag

class Answers(db.Model):
	questionName = db.StringProperty(required=True)
	questionUser = db.StringProperty(required=True)
	answerName = db.StringProperty(required=True)
	answerUser = db.StringProperty(required=True)
	answerContent = db.StringProperty(required=True)
	answerTime = db.TimeProperty(auto_now_add=True)

class Votes(db.Model):
	questionName = db.StringProperty(required=True)
	questionUser = db.StringProperty(required=True)
	answerName = db.StringProperty()
	answerUser = db.StringProperty()
	voteUser = db.StringProperty(required=True)
	voteTime = db.DateProperty(auto_now_add=True)
	voteType = db.StringProperty(required=True, choices=set(["up", "down"]))


class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        existing = db.GqlQuery("SELECT * FROM User WHERE userid = :1",user)
        existing = User.all()
        existing.filter("userid =", user)
        self.response.out.write('<html><body>')
        if user:
        	if existing == "":
        		newuser = User(userid = user)
        		newuser.put()
        	self.response.out.write('Welcome, %s! (<a href="%s">sign out</a>)' %
                        (user.nickname(), users.create_logout_url('/')))
        	self.response.out.write('</br><a href="/question">Create New Question</a>')
        	newquestion = Questions(questionName="test question",questionUser=user.nickname(),questionContent="Test now")
        	newquestion.put()
            
        else:
            self.response.out.write('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))

        questions=db.GqlQuery("SELECT * FROM Questions ORDER BY questionTime DESC")
        self.response.out.write('<table style="width:100%">')
        self.response.out.write('<tr><td>question time</td><td>User</td><td>Title</td><td>Content</td></tr>')
        for question in questions:
        	self.response.out.write('<tr><td>%s</td><td>%s</td><td><a href="/%s">%s</a></td><td>%s</td></tr>' %
        		(question.questionTime,question.questionUser,question.questionName,question.questionName,question.questionContent))
        self.response.out.write('</table>')
        self.response.out.write('</html></body>')

Create_Question_PAGE_FOOTER_TEMPLATE = """\
    <form action="/newquestion" method="post">
      <div>Question Name: <textarea name="name"></textarea></div>
      <div>Your Question: <textarea name="content" rows="3" cols="60"></textarea></div>
      <div><input type="submit" value="Submit Question"></div>
    </form>
  </body>
</html>
"""

class Question(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        self.response.out.write('<html><body>')
        if user:
        	self.response.write(Create_Question_PAGE_FOOTER_TEMPLATE %
                            (sign_query_params, cgi.escape(guestbook_name),
                             url, url_linktext))
            
        else:
            self.response.out.write('<a href="%s">Sign in or register</a>.' %
                        users.create_login_url('/'))

        self.response.out.write('</html></body>')

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/question', Question),
    ('/newquestion',MainPage),
], debug=True)
