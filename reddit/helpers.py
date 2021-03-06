# This file is part of reddit_api.
#
# reddit_api is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# reddit_api is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with reddit_api.  If not, see <http://www.gnu.org/licenses/>.

import urllib
import urllib2
from urlparse import urljoin

from reddit.decorators import SleepAfter, require_login
from reddit.util import Memoize


def _get_section(subpath=''):
    """
    Used by the Redditor class to generate each of the sections (overview,
    comments, submitted).
    """
    def _section(self, sort='new', time='all', limit=0, place_holder=None):
        data = {'sort': sort, 'time': time}
        url = urljoin(self._url, subpath)  # pylint: disable-msg=W0212
        return self.reddit_session.get_content(url, limit=limit, url_data=data,
                                               place_holder=place_holder)
    return _section


def _get_sorter(subpath='', **defaults):
    """
    Used by the Reddit Page classes to generate each of the currently supported
    sorts (hot, top, new, best).
    """
    def _sorted(self, limit=0, place_holder=None, **data):
        for key, value in defaults.items():
            if key == 'time':
                # time should be 't' in the API data dict
                key = 't'
            data.setdefault(key, value)
        url = urljoin(self._url, subpath)  # pylint: disable-msg=W0212
        return self.reddit_session.get_content(url, limit=limit, url_data=data,
                                               place_holder=place_holder)
    return _sorted


def _modify_relationship(relationship, unlink=False):
    """
    Modify the relationship between the current user or subreddit and a target
    thing.

    Used to support friending (user-to-user), as well as moderating,
    contributor creating, and banning (user-to-subreddit).
    """
    # the API uses friend and unfriend to manage all of these relationships
    url_key = 'unfriend' if unlink else 'friend'

    @require_login
    def do_relationship(thing, user, **kwargs):
        params = {'name': str(user),
                  'container': thing.content_id,
                  'type': relationship,
                  'uh': thing.reddit_session.modhash,
                  'api_type': 'json'}
        params.update(kwargs)  # HACK: for make_moderator to prevent an error
        url = thing.reddit_session.config[url_key]
        return thing.reddit_session.request_json(url, params)
    return do_relationship


@Memoize
@SleepAfter
def _request(reddit_session, page_url, params=None, url_data=None):
    if url_data:
        page_url += '?' + urllib.urlencode(url_data)
    encoded_params = None
    if params:
        params = dict([k, v.encode('utf-8')] for k, v in params.items())
        encoded_params = urllib.urlencode(params)
    if isinstance(page_url, unicode):
        page_url = urllib.quote(page_url.encode('utf-8'), ':/')
    request = urllib2.Request(page_url, data=encoded_params,
                              headers=reddit_session.DEFAULT_HEADERS)
    # pylint: disable-msg=W0212
    response = reddit_session._opener.open(request)
    return response.read()
