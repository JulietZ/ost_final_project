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
import re
from google.appengine.api import users
from google.appengine.ext import ndb
import webapp2
import os
import jinja2
from jinja2 import Environment, FileSystemLoader
import datetime
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers
from google.appengine.api import images

JINJA_ENVIRONMENT = Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

def html_display(string):
    temp = re.sub(r'(\https?://[^\s<>"]+)', r'<a href="\1">\1</a>', string)
    string = re.sub(r'<a href="(\https?://[^\s<>"]+)">[^\s]+.(jpg|png|gif)</a>', r'<img src="\1">', temp)
    return string

JINJA_ENVIRONMENT.filters['html_display'] = html_display

class Questions(ndb.Model):
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    createDate = ndb.DateTimeProperty(auto_now_add=True)
    title = ndb.StringProperty(indexed=False)
    modifyDate = ndb.DateTimeProperty()
    tag = ndb.StringProperty(repeated=True)
    voteScore = ndb.IntegerProperty()
    img = ndb.BlobKeyProperty()
    imgUrl = ndb.StringProperty()

class FollowQuestions(ndb.Model):
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    createDate = ndb.DateTimeProperty(auto_now_add=True)
    title = ndb.StringProperty(indexed=False)
    modifyDate = ndb.DateTimeProperty()
    voteScore = ndb.IntegerProperty()
    qtitle = ndb.StringProperty(indexed=False)
    img = ndb.BlobKeyProperty()
    imgUrl = ndb.StringProperty()
    
class Answers(ndb.Model):
    author = ndb.UserProperty()
    title = ndb.StringProperty(indexed=False)
    content = ndb.StringProperty(indexed=False)
    createDate = ndb.DateTimeProperty(auto_now_add=True)
    modifyDate = ndb.DateTimeProperty()
    voteScore = ndb.IntegerProperty()
    qtitle = ndb.StringProperty(indexed=False)
    img = ndb.BlobKeyProperty()
    imgUrl = ndb.StringProperty()

class Votes(ndb.Model):
    author = ndb.UserProperty(required=True)
    createDate = ndb.DateTimeProperty(auto_now_add=True)
    voteType = ndb.StringProperty(choices=set(["question", "fquestion", "answer"]))
    voteValue = ndb.StringProperty(choices=set(["up", "down"]))


class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)

        else:
            url = users.create_login_url(self.request.uri)

        submit_url = blobstore.create_upload_url('/question')
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
            'previous': previouspage,
            'submit_url':submit_url
        }
        template = JINJA_ENVIRONMENT.get_template('mainpage.html')
        self.response.write(template.render(template_values))

class QuestionDetail(webapp2.RequestHandler):
    def get(self):
        user=users.get_current_user()
        if user:
            url = users.create_logout_url(self.request.uri)

        else:
            url = users.create_login_url(self.request.uri)
        questionKey=self.request.get('questionKey')
        question=ndb.Key(urlsafe = questionKey).get()
        template_values = {
            'user': user,
            'question': question,
            'url': url
        }
        template = JINJA_ENVIRONMENT.get_template('detail.html')
        self.response.write(template.render(template_values))

class CreateQuestion(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        if self.request.get('efquestion'):
            fquestionKey=self.request.get('efquestion')
            fquestion=ndb.Key(urlsafe = fquestionKey).get()
            fquestion.title=self.request.get('eftitle')
            fquestion.content=self.request.get('efcontent')
            fquestion.modifyDate=datetime.datetime.now()
            submitimg=self.get_uploads('fimg')
            if submitimg:
                blob_info = submitimg[0]
                fquestion.img = blob_info.key()
                imgtype = blob_info.filename[-4:].lower()
                fquestion.imgUrl = images.get_serving_url(blob_info.key())+imgtype
            fquestion.put()
            self.redirect('/personal')

        elif self.request.get('equestion'):
            questionKey=self.request.get('equestion')
            question=ndb.Key(urlsafe = questionKey).get()
            question.title=self.request.get('eqtitle')
            question.content=self.request.get('eqcontent')
            question.tag=self.request.get('eqtag',allow_multiple=True)
            question.modifyDate=datetime.datetime.now()
            submitimg=self.get_uploads('qimg')
            if submitimg:
                blob_info = submitimg[0]
                question.img = blob_info.key()
                imgtype = blob_info.filename[-4:].lower()
                question.imgUrl = images.get_serving_url(blob_info.key())+imgtype
            question.put()
            redirectURL = "/view?questionKey=%s" % questionKey
            self.redirect(redirectURL)

        elif self.request.get('fquestion'):
            questionKey=self.request.get('fquestion')
            question=ndb.Key(urlsafe = questionKey).get()
            fquestion=FollowQuestions(parent=ndb.Key(urlsafe=questionKey))
            fquestion.author = users.get_current_user()
            fquestion.title = self.request.get('qtitle')
            fquestion.content = self.request.get('qcontent')
            fquestion.voteScore = 0
            fquestion.qtitle=question.title
            fquestion.modifyDate=datetime.datetime.now()
            submitimg=self.get_uploads('qimg')
            if submitimg:
                blob_info = submitimg[0]
                fquestion.img = blob_info.key()
                imgtype = blob_info.filename[-4:].lower()
                fquestion.imgUrl = images.get_serving_url(blob_info.key())+imgtype
            fquestion.put()
            redirectURL = "/view?questionKey=%s" % questionKey
            self.redirect(redirectURL)

        else:
            question=Questions()
            question.author = users.get_current_user()
            question.title = self.request.get('qtitle')
            question.content = self.request.get('qcontent')
            question.voteScore = 0
            question.tag = self.request.get('qtag', allow_multiple=True)
            question.modifyDate=datetime.datetime.now()
            submitimg=self.get_uploads('qimg')
            if submitimg:
                blob_info = submitimg[0]
                question.img = blob_info.key()
                imgtype = blob_info.filename[-4:].lower()
                question.imgUrl = images.get_serving_url(blob_info.key())+imgtype
            question.put()
            redirectURL = "/view?questionKey=%s" % question.key.urlsafe()
            self.redirect(redirectURL)

class CreateAnswer(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        if self.request.get('eanswer'):
            answerKey=self.request.get('eanswer')
            answer=ndb.Key(urlsafe = answerKey).get()
            answer.title=self.request.get('eatitle')
            answer.content=self.request.get('eacontent')
            answer.modifyDate=datetime.datetime.now()
            submitimg=self.get_uploads('aimg')
            if submitimg:
                blob_info = submitimg[0]
                answer.img = blob_info.key()
                imgtype = blob_info.filename[-4:].lower()
                answer.imgUrl = images.get_serving_url(blob_info.key())+imgtype
            answer.put()
            self.redirect('/personal')

        elif self.request.get('atitle'):
            questionKey=self.request.get('questionKey')
            question=ndb.Key(urlsafe = questionKey).get()
            answer=Answers(parent=ndb.Key(urlsafe=questionKey))
            answer.author = users.get_current_user()
            answer.title = self.request.get('atitle')
            answer.content = self.request.get('acontent')
            answer.voteScore = 0
            answer.modifyDate=datetime.datetime.now()
            answer.qtitle=question.title
            submitimg=self.get_uploads('aimg')
            if submitimg:
                blob_info = submitimg[0]
                answer.img = blob_info.key()
                imgtype = blob_info.filename[-4:].lower()
                answer.imgUrl = images.get_serving_url(blob_info.key())+imgtype
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
        fquestion_qry = FollowQuestions.query(FollowQuestions.author == user).order(-FollowQuestions.modifyDate)
        fquestions=fquestion_qry.fetch()
        template_values = {
            'user': user,
            'questions': questions,
            'answers': answers,
            'fquestions': fquestions
        }
        template = JINJA_ENVIRONMENT.get_template('homepage.html')
        self.response.write(template.render(template_values))        

class Edit(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        if self.request.get('create'):
            questionKey=self.request.get('questionKey')
            question=ndb.Key(urlsafe = questionKey).get()
            submit_url = blobstore.create_upload_url('/question')
            template_values = {
                    'user': user,
                    'question': question,
                    'following': "following",
                    'submit_url': submit_url
                }

        else:
            if self.request.get('questionKey'):
                submit_url = blobstore.create_upload_url('/question')
                questionKey=self.request.get('questionKey')
                question=ndb.Key(urlsafe = questionKey).get()
                template_values = {
                    'user': user,
                    'question': question,
                    'submit_url': submit_url
                }
            elif self.request.get('fquestionKey'):
                submit_url = blobstore.create_upload_url('/question')
                fquestionKey=self.request.get('fquestionKey')
                fquestion=ndb.Key(urlsafe = fquestionKey).get()
                template_values = {
                    'user': user,
                    'fquestion': fquestion,
                    'submit_url': submit_url
                }
            else:
                submit_url = blobstore.create_upload_url('/answer')
                answerKey=self.request.get('answerKey')
                answer=ndb.Key(urlsafe = answerKey).get()
                template_values = {
                    'user': user,
                    'answer': answer,
                    'submit_url': submit_url
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
        submit_url = blobstore.create_upload_url('/answer')

        if self.request.get('questionKey'):
            questionKey=self.request.get('questionKey')
            question=ndb.Key(urlsafe = questionKey).get()
            answers = Answers.query(ancestor=question.key).order(-Answers.voteScore).fetch()
            fquestions = FollowQuestions.query(ancestor=question.key).order(-FollowQuestions.modifyDate).fetch()
            template_values = {
                'user': user,
                'question': question,
                'answers': answers,
                'url': url,
                'submit_url':submit_url,
                'fquestions':fquestions
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

        elif self.request.get('fquestionKey'):
            fquestionKey=self.request.get('fquestionKey')
            fquestion=ndb.Key(urlsafe = fquestionKey).get()
            vote = Votes.query(Votes.author==user, Votes.voteType=="fquestion", ancestor=fquestion.key).get()
            if vote:
                if vote.voteValue=="down":
                    fquestion.voteScore=fquestion.voteScore+2
                    vote.voteValue="up"
                    vote.put()
            else:
                fquestion.voteScore=fquestion.voteScore+1
                vote = Votes(parent=ndb.Key(urlsafe=self.request.get('fquestionKey')))
                vote.author=user
                vote.voteValue="up"
                vote.voteType="fquestion"
                vote.put()
            fquestion.put()

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

        elif self.request.get('fquestionKey'):
            fquestionKey=self.request.get('fquestionKey')
            fquestion=ndb.Key(urlsafe = fquestionKey).get()
            vote = Votes.query(Votes.author==user, Votes.voteType=="fquestion", ancestor=fquestion.key).get()
            if vote:
                if vote.voteValue=="up":
                    fquestion.voteScore=fquestion.voteScore-2
                    vote.voteValue="down"
                    vote.put()
            else:
                fquestion.voteScore=fquestion.voteScore-1
                vote = Votes(parent=ndb.Key(urlsafe=self.request.get('fquestionKey')))
                vote.author=user
                vote.voteValue="down"
                vote.voteType="fquestion"
                vote.put()
            fquestion.put()

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


class Delete(webapp2.RequestHandler):
    def get(self):
        if self.request.get('questionKey'):
            try:
                questionKey=self.request.get('questionKey')
                question=ndb.Key(urlsafe = questionKey).get()
                fquestions = FollowQuestions.query(ancestor=question.key).fetch()
                answers = Answers.query(ancestor=question.key).fetch()
                votes = Votes.query(ancestor=question.key).fetch()
                for fquestion in fquestions:
                    fquestion.key.delete()
                for answer in answers:
                    answer.key.delete()
                for vote in votes:
                    vote.key.delete()
                question.key.delete()
                self.redirect('/personal')
            except:
                self.redirect('/personal')
                return
        elif self.request.get('fquestionKey'):
            try:
                fquestionKey=self.request.get('fquestionKey')
                fquestion=ndb.Key(urlsafe = fquestionKey).get()
                votes = Votes.query(ancestor=fquestion.key).fetch()
                for vote in votes:
                    vote.key.delete()
                fquestion.key.delete()
                self.redirect('/personal')
            except:
                self.redirect('/personal')
                return
        elif self.request.get('answerKey'):
            try:
                answerKey=self.request.get('answerKey')
                answer=ndb.Key(urlsafe = answerKey).get()
                votes = Votes.query(ancestor=answer.key).fetch()
                for vote in votes:
                    vote.key.delete()
                answer.key.delete()
                self.redirect('/personal')
            except:
                self.redirect('/personal')
                return
        else:
            self.redirect('/personal')

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/tag', MainPage),
    ('/detail',QuestionDetail),
    ('/question', CreateQuestion),
    ('/answer', CreateAnswer),
    ('/personal', Personal),
    ('/edit', Edit),
    ('/view', ViewQuestion),
    ('/voteUp', VoteUp),
    ('/voteDown', VoteDown),
    ('/delete',Delete)
], debug=True)

