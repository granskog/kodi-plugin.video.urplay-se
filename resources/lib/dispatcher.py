# -*- coding: utf-8 -*-
import sys
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import re
import util
log = util.Logger()

class Dispatcher(object):
    _routes = None
    def __init__(self, baseURL, routes):
        self._baseURL = baseURL
        self._routes = routes

    def dispatch(self, url):
        if self._routes is None: return

        # Separate the base URL
        uri = url.split(self._baseURL)[-1]

        for template, handlerClass in self._routes:

            # Make shure the regex match at start of string to the end of the string.
            if not template.startswith('^'):
                template = '^' + template

            if not template.endswith('$'):
                template += '$'

            log.debug('Testing template: r"{0}" against URL: "{1}"'.format(template, uri))
            match = re.match(template, uri)

            if match:

                log.debug('Match for: r"{0}". Groups: {1}.'.format(template, match.groups()))
                h = handlerClass(*match.groups())
                h.process()
                break;

        else:
            log.debug('No url handler matched "{0}"!'.format(url))