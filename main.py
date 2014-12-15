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
    return ndb.Key('Site', 'default')

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
    title = ndb.StringProperty(indexed=False)
    content = ndb.StringProperty(indexed=False)
    createDate = ndb.DateTimeProperty(auto_now_add=True)
    modifyDate = ndb.DateTimeProperty()
    voteScore = ndb.IntegerProperty()

class Votes(ndb.Model):
    author = ndb.UserProperty(required=True)
    createDate = ndb.DateTimeProperty(auto_now_add=True)
    voteType = ndb.StringProperty(choices=set(["question", "answer"]))
    voteValue = ndb.StringProperty(choices=set(["up", "down"]))


class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)

        else:
            url = users.create_login_url(self.request.uri)

        if self.request.get('type'):
            qtype=self.request.get('type')
            questions_query = Questions.query(Questions.tag==qtype).order(-Questions.modifyDate)
        else:
            questions_query = Questions.query().order(-Questions.modifyDate)
        lenquestion = questions_query.fetch()
        #questions = questions_query.fetch()
        pageno=1
        pagesize=10
        nextpage=False
        previouspage=False
        if len(lenquestion)>0:
            if self.request.get('pageno'):
                pageno=int(self.request.get('pageno'))
            if self.request.get('nextpage'):
                pageno=pageno+1
            if self.request.get('previouspage'):
                pageno=pageno-1
            if pageno>1:
                previouspage=True
            if len(lenquestion)>(pagesize*pageno):
                nextpage=True
                temp=pagesize
            else:
                temp=len(lenquestion)-(pagesize*(pageno-1))
            questions = questions_query.fetch(temp,offset=(pageno-1)*pagesize)
        else:
            questions = lenquestion
        
        template_values = {
            'user': users.get_current_user(),
            'questions': questions,
            'url': url,
            'pageno': pageno,
            'next': nextpage,
            'previous': previouspage
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
            question.modifyDate=datetime.datetime.now()
            question.put()
            self.redirect('/personal')

        elif self.request.get('qtitle'):
            question=Questions()
            question.author = users.get_current_user()
            question.title = self.request.get('qtitle')
            question.content = self.request.get('qcontent')
            question.voteScore = 0
            question.tag = self.request.get('qtag', allow_multiple=True)
            question.modifyDate=datetime.datetime.now()
            question.put()
            self.redirect('/')

class CreateAnswer(webapp2.RequestHandler):
    def post(self):
        if self.request.get('eanswer'):
            answerKey=self.request.get('eanswer')
            answer=ndb.Key(urlsafe = answerKey).get()
            answer.title=self.request.get('eatitle')
            answer.content=self.request.get('eacontent')
            answer.modifyDate=datetime.datetime.now()
            answer.put()
            self.redirect('/personal')

        elif self.request.get('atitle'):
            answer=Answers(parent=ndb.Key(urlsafe=self.request.get('questionKey')))
            answer.author = users.get_current_user()
            answer.title = self.request.get('atitle')
            answer.content = self.request.get('acontent')
            answer.voteScore = 0
            answer.modifyDate=datetime.datetime.now()
            answer.put()
            redirectURL = "/view?questionKey=%s" % self.request.get('questionKey')
            self.redirect(redirectURL)

class Personal(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        question_qry = Questions.query(Questions.author == user).order(-Questions.modifyDate)
        questions=question_qry.fetch()
        answer_qry = Answers.query(Answers.author == user).order(-Answers.voteScore)
        answers=answer_qry.fetch()
        template_values = {
            'user': user,
            'questions': questions,
            'answers': answers
        }
        template = JINJA_ENVIRONMENT.get_template('homepage.html')
        self.response.write(template.render(template_values))        

class Edit(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if self.request.get('questionKey'):
            questionKey=self.request.get('questionKey')
            question=ndb.Key(urlsafe = questionKey).get()
            template_values = {
                'user': user,
                'question': question
            }
        else:
            answerKey=self.request.get('answerKey')
            answer=ndb.Key(urlsafe = answerKey).get()
            template_values = {
                'user': user,
                'answer': answer
            }
        template = JINJA_ENVIRONMENT.get_template('edit.html')
        self.response.write(template.render(template_values))

class ViewQuestion(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)

        else:
            url = users.create_login_url(self.request.uri)

        if self.request.get('questionKey'):
            questionKey=self.request.get('questionKey')
            question=ndb.Key(urlsafe = questionKey).get()
            answers = Answers.query(ancestor=question.key).order(-Answers.voteScore).fetch()
            template_values = {
                'user': user,
                'question': question,
                'answers': answers,
                'url': url
            }
            template = JINJA_ENVIRONMENT.get_template('view.html')
            self.response.write(template.render(template_values))

class VoteUp(webapp2.RequestHandler):
    def get(self):
        user=users.get_current_user()
        questionKey=self.request.get('questionKey')
        if self.request.get('answerKey'):
            answerKey=self.request.get('answerKey')
            answer=ndb.Key(urlsafe = answerKey).get()
            vote = Votes.query(Votes.author==user, Votes.voteType=="answer", ancestor=answer.key).get()
            if vote:
                if vote.voteValue=="down":
                    answer.voteScore=answer.voteScore+2
                    vote.voteValue="up"
                    vote.put()
            else:
                answer.voteScore=answer.voteScore+1
                vote = Votes(parent=ndb.Key(urlsafe=self.request.get('answerKey')))
                vote.author=user
                vote.voteValue="up"
                vote.voteType="answer"
                vote.put()
            answer.put()

        else:
            question=ndb.Key(urlsafe = questionKey).get()
            vote = Votes.query(Votes.author==user, Votes.voteType=="question", ancestor=question.key).get()
            if vote:
                if vote.voteValue=="down":
                    question.voteScore=question.voteScore+2
                    vote.voteValue="up"
                    vote.put()

            else:
                question.voteScore=question.voteScore+1
                vote = Votes(parent=ndb.Key(urlsafe=self.request.get('questionKey')))
                vote.author=user
                vote.voteValue="up"
                vote.voteType="question"
                vote.put()
            question.put()
        redirectURL = "/view?questionKey=%s" % self.request.get('questionKey')
        self.redirect(redirectURL)

class VoteDown(webapp2.RequestHandler):
    def get(self):
        user=users.get_current_user()
        questionKey=self.request.get('questionKey')
        if self.request.get('answerKey'):
            answerKey=self.request.get('answerKey')
            answer=ndb.Key(urlsafe = answerKey).get()
            vote = Votes.query(Votes.author==user, Votes.voteType=="answer", ancestor=answer.key).get()
            if vote:
                if vote.voteValue=="up":
                    answer.voteScore=answer.voteScore-2
                    vote.voteValue="down"
                    vote.put()
            else:
                answer.voteScore=answer.voteScore-1
                vote = Votes(parent=ndb.Key(urlsafe=self.request.get('answerKey')))
                vote.author=user
                vote.voteValue="down"
                vote.voteType="answer"
                vote.put()
            answer.put()

        else:
            question=ndb.Key(urlsafe = questionKey).get()
            vote = Votes.query(Votes.author==user, Votes.voteType=="question", ancestor=question.key).get()
            if vote:
                if vote.voteValue=="up":
                    question.voteScore=question.voteScore-2
                    vote.voteValue="down"
                    vote.put()

            else:
                question.voteScore=question.voteScore-1
                vote = Votes(parent=ndb.Key(urlsafe=self.request.get('questionKey')))
                vote.author=user
                vote.voteValue="down"
                vote.voteType="question"
                vote.put()
            question.put()
        redirectURL = "/view?questionKey=%s" % self.request.get('questionKey')
        self.redirect(redirectURL)

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/tag', MainPage),
    ('/question', CreateQuestion),
    ('/answer', CreateAnswer),
    ('/personal', Personal),
    ('/edit', Edit),
    ('/view', ViewQuestion),
    ('/voteUp', VoteUp),
    ('/voteDown', VoteDown)
], debug=True)

