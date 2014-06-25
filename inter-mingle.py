import os
import urllib

from google.appengine.api import users
from google.appengine.ext import ndb

import jinja2
import webapp2


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

DEFAULT_GROUP_NAME = 'default_group'

# We set a parent key on the 'Greetings' to ensure that they are all in the same
# entity group. Queries across the single entity group will be consistent.
# However, the write rate should be limited to ~1/second.

def group_key(group_name=DEFAULT_GROUP_NAME):
    """Constructs a Datastore key for a Guestbook entity with guestbook_name."""
    return ndb.Key('Group', group_name)

class Message(ndb.Model):
    """Models an individual Guestbook entry."""
    author = ndb.UserProperty()
    content = ndb.StringProperty(indexed=False)
    date = ndb.DateTimeProperty(auto_now_add=True)

class MainPage(webapp2.RequestHandler):

    def get(self):
        group_name = self.request.get('group_name',
                                          DEFAULT_GROUP_NAME)
        mquery = Message.query(
            ancestor=group_key(group_name)).order(-Message.date)
        messages = mquery.fetch(5)

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        template_values = {
            'messages': messages,
            'group_name': urllib.quote_plus(group_name),
            'url': url,
            'url_linktext': url_linktext,
        }

        template = JINJA_ENVIRONMENT.get_template('minglepage.html')
        self.response.write(template.render(template_values))

class Group(webapp2.RequestHandler):
    def post(self):
        # We set the same parent key on the 'Greeting' to ensure each Greeting
        # is in the same entity group. Queries across the single entity group
        # will be consistent. However, the write rate to a single entity group
        # should be limited to ~1/second.
        group_name = self.request.get('group_name',
                                          DEFAULT_GROUP_NAME)
        message = Message(parent=group_key(group_name))

        if users.get_current_user():
            greeting.author = users.get_current_user()

        message.content = self.request.get('content')
        message.put()

        query_params = {'group_name': group_name}
        self.redirect('/?' + urllib.urlencode(query_params))

application = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/write', Group),
], debug=True)