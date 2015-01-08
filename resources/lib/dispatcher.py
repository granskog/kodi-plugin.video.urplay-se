# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
import util
log = util.Logger()

class Dispatcher(object):
    _routes = None
    def __init__(self, plugin, routes):
        self._plugin = plugin
        self._routes = routes

    def dispatch(self, url):
        if self._routes is None: return

        path = url
        if isinstance(path, util.URL):
            path = url.url

        for template, handlerClass in self._routes:

            # Make shure the regex match at start of string to the end of the string.
            if not template.startswith('^'):
                template = '^' + template

            if not template.endswith('$'):
                template += '$'

            log.debug('Testing template: r"{0}" against path: "{1}"'.format(template, path))
            match = re.match(template, path)

            if match:

                log.debug('Match for: r"{0}". Groups: {1}.'.format(template, match.groups()))
                h = handlerClass(self._plugin, url)
                h.process()
                break;

        else:
            log.debug('No url handler matched "{0}"!'.format(url))