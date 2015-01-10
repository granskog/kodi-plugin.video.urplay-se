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
import inspect
import urllib

class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

class Logger(object):
    __metaclass__ = Singleton
    _log_func = None

    def __init__(self, log_func = None, name='Logger', lvlDeb=0, lvlInfo=1, lvlWarn=2, lvlErr=3):
        self.setupLogger(log_func, name, lvlDeb, lvlInfo, lvlWarn, lvlErr)

    def setupLogger(self, log_func = None, name='Logger', lvlDeb=0, lvlInfo=1, lvlWarn=2, lvlErr=3):
        self._log_func = log_func or self._default_log_func
        self._name = name
        self._DEBUG = lvlDeb
        self._INFO = lvlInfo
        self._WARN = lvlWarn
        self._ERR = lvlErr

    def _default_log_func(self, msg, lvl):
        print lvl, ': ', msg

    def _log(self, tmpl, msg, lvl):
        self._log_func(tmpl.format(self._name, msg), lvl)

    def log(self, msg, lvl):
        self._log('[{0}]: {1}', msg, lvl)

    def info(self, msg):
        self.log(msg, self._INFO)

    def warning(self, msg):
        self.log(msg, self._WARN)

    def error(self, msg):
        self.log(msg, self._ERR)

    def debug(self, msg):
        fle = inspect.stack()[1][1].split('/')[-1]
        line = inspect.stack()[1][2]
        self._log('[{{0}} ({0}, line {1})]: {{1}}'.format(fle, line), msg, self._DEBUG)

class URL(object):
    def __init__(self, url = None, **kwargs):
        if isinstance(url, URL):
            self.url  = url.url
            self.args = dict(url.args)
            self.args.update(kwargs)
        else:
            self.url = url or ''
            self.args = kwargs

    def __add__(self, rhs):
        args = dict(self.args)
        args.update(rhs.args)
        return URL(self.url + rhs.url, **args)

    def __str__(self):
        args = ''
        if self.args:
            args = '?' + urllib.urlencode(self.args)
        return urllib.quote(self.url, safe = str('/:')) + args

    def extend(self, path):
        self.url += path

def safeListGet (l, idx, default):
    try:
        return l[idx]
    except IndexError:
        return default