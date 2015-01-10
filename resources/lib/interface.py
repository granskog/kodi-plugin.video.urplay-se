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
import xbmcplugin

from util import Logger, URL

log = Logger()

class BaseHandler(object):
    def __init__(self, plugin, path):
        self._plugin = plugin
        self._path = path
        super(BaseHandler, self).__init__()

    def process(self):
        raise NotImplementedError

class Directory(BaseHandler):
    def _fetch(self):
        raise NotImplementedError

    def process(self):
        log.debug('Start updating folder for "{0}".'.format(self._path))
        # Unfortunately xbmcplugin.addDirectoryItems() does not work with generators.
        # It expects a list, so call list() on the generator object.
        items = list(self._fetch())
        if items:
            xbmcplugin.addDirectoryItems(self._plugin.handle, items)
            xbmcplugin.endOfDirectory(self._plugin.handle)
            log.debug('Done updating folder for "{0}".'.format(self._path))
        else:
            log.warning('No items retreived for path: '.format(self._path))
            xbmcplugin.endOfDirectory(self._plugin.handle, succeeded = False)

class URLBuilder(type):
    def __init__(cls, name, bases, attrs):
        urlRoot = getattr(bases[0], "url", None)
        if not 'url' in attrs:
            cls.url = URL(urlRoot)
        elif urlRoot is not None:
            cls.url = urlRoot + cls.url
        super(URLBuilder, cls).__init__(name, bases, attrs)

class WebEnabled(object):
    __metaclass__ = URLBuilder
    _html = None

    @property
    def html(self):
        if not self._html:
            log.info('Fetching content from "{0}".'.format(self.url))
            try:
                request = urllib2.Request(unicode(self.url))
                response = urllib2.urlopen(request)
            except (urllib2.URLError, urllib2.HTTPError), e:
                log.error('Unable to fetch content from "{0}" ({1}).'.format(self.url, e))
                return None
            charset = response.headers['content-type'].split('charset=')[-1]
            try:
                self._html = response.read().decode(charset)
            except LookupError:
                log.error('Unknown charset ({0}) in header, trying utf-8.'.format(charset))
                try:
                    self._html = response.read().decode('utf-8')
                except UnicodeError:
                    log.error('Unable decode content using utf-8.')
                    return None
            log.debug('Received response, ok!')
        return self._html