import cgi
import urllib
import datetime

from google.appengine.api import users
from google.appengine.ext import ndb

import webapp2

MAIN_PAGE_FOOTER_TEMPLATE = """\
    <form action="/write?%s" method="post">
      <div><textarea name="content" rows="2" cols="60"></textarea></div>
      <div><input type="submit" value="Post"></div>
    </form>
    <hr>
    <form>Group name:
      <input value="%s" name="group_name">
      <input type="submit" value="Switch">
    </form>
    <a href="%s">%s</a>
  </body>
</html>
"""

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
        self.response.write('<html><body>')
        group_name = self.request.get('group_name',
                                          DEFAULT_GROUP_NAME)

        # Ancestor Queries, as shown here, are strongly consistent with the High
        # Replication Datastore. Queries that span entity groups are eventually
        # consistent. If we omitted the ancestor from this query there would be
        # a slight chance that Greeting that had just been written would not
        # show up in a query.
        message_query = Message.query(
            ancestor=group_key(group_name)).order(-Message.date)
        messages = message_query.fetch(3)

        for msg in messages:

            self.response.write('%s' % msg.date.strftime('%d %b %y - %I.%M.%S %p'))
            self.response.write('<blockquote>%s</blockquote>' %
                                cgi.escape(msg.content))
            

        if users.get_current_user():
            url = users.create_logout_url(self.request.uri)
            url_linktext = 'Logout'
        else:
            url = users.create_login_url(self.request.uri)
            url_linktext = 'Login'

        # Write the submission form and the footer of the page
        sign_query_params = urllib.urlencode({'group_name': group_name})
        self.response.write(MAIN_PAGE_FOOTER_TEMPLATE %
                            (sign_query_params, cgi.escape(group_name),
                             url, url_linktext))

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