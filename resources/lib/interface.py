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

    def onException(self, e):
        raise NotImplementedError

class Directory(BaseHandler):
    def _fetch(self):
        raise NotImplementedError

    def process(self):
        log.debug('Start updating folder for "{0}".'.format(self._path))
        
        items = self._fetch()
        # Unfortunately addDirectoryItems() does not work with generators.
        # It expect a list, so call list() on the generator object.
        xbmcplugin.addDirectoryItems(self._plugin.handle, list(items))
        xbmcplugin.endOfDirectory(self._plugin.handle)

        log.debug('Done updating folder for "{0}".'.format(self._path))

    def onException(self, e):
        xbmcplugin.endOfDirectory(self._plugin.handle, succeeded = False)
        return False

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
            request = urllib2.Request(str(self.url))
            response = urllib2.urlopen(request)
            self._html = response.read()
            log.debug('Received response, ok!')
        return self._html