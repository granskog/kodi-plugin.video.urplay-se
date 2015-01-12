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
                h.execute()
                break;

        else:
            log.debug('No url handler matched "{0}"!'.format(url))