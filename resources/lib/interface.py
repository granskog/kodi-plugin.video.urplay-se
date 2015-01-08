# -*- coding: utf-8 -*-
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
                request = urllib2.Request(str(self.url))
                response = urllib2.urlopen(request)
            except (urllib2.URLError, urllib2.HTTPError) as e:
                log.error('Unable to fetch content from "{0}" ({1}).'.format(self.url, e))
            else:
                self._html = response.read()
                log.debug('Received response, ok!')
        return self._html