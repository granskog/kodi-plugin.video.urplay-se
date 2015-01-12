# -*- coding: utf-8 -*-

# This file is part of 'UR Play Video Plugin' for Kodi Media Player, henceforth 'this program'.
# Copyright (C) 2015 David Gran Skog
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Foobar.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
import urllib2

from util import Logger, URL

log = Logger()

class HandlingError(Exception):
    def __init__(self,msg, code):
        self.msgCode = code
        super(HandlingError, self).__init__(msg)
    pass

class BaseHandler(object):
    def __init__(self, plugin, path):
        self._plugin = plugin
        self._path = path
        super(BaseHandler, self).__init__()

    def execute(self):
        raise NotImplementedError

class URLBuilder(type):
    def __init__(cls, name, bases, attrs):
        urlRoot = getattr(bases[0], "url", None)
        if not 'url' in attrs:
            cls.url = URL(urlRoot)
        elif urlRoot is not None:
            cls.url = urlRoot + cls.url
        super(URLBuilder, cls).__init__(name, bases, attrs)

class ConnectionError(Exception):
    pass

class WebEnabled(object):
    __metaclass__ = URLBuilder
    html = None

    def fetchHTML(self):
        log.info('Fetching content from "{0}".'.format(self.url))
        try:
            request = urllib2.Request(unicode(self.url), headers = {'User-Agent': 'Mozilla/5.0'})
            response = urllib2.urlopen(request)
            html = response.read()
        except (urllib2.URLError, urllib2.HTTPError), e:
            log.error('Unable to fetch content from "{0}" ({1}).'.format(self.url, e))
            raise ConnectionError(e)

        # This should really be handled better. There is no check for charset in actual
        # html response. Also guessing charsets is not that nice really. But for now, it will
        # have to do.
        charset = response.headers['content-type'].split('charset=')[-1]
        try:
            html = html.decode(charset)
        except LookupError:
            charsets = ['utf-8', 'cp1252', 'latin-1']
            log.error('Unknown charset ("{0}") in header, trying one of these: {1}.'.format(charset, charsets))
            for charset in charsets:
                try:
                    html = html.decode(charset)
                    break
                except UnicodeError:
                    log.warning('Unable decode content using "{0}".'.format(charset))
                    continue
            else:
                raise ConnectionError('Unable to decode content.')

        self.html = html
        log.debug('Received response, ok!')

        return self.html
