# -*- coding: utf-8 -*-
import inspect

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

    def _log(self, msg, lvl):
        self._log_func('[{0}] @"{1}": {2}'.format(self._name, inspect.stack()[2][3], msg), lvl)

    def info(self, msg):
        self._log(msg, self._INFO)

    def warning(self, msg):
        self._log(msg, self._WARN)

    def error(self, msg):
        self._log(msg, self._ERR)

    def debug(self, msg):
        self._log(msg, self._DEBUG)