# -*- coding: utf-8 -*-
from resources.lib.parsedom import parseDOM
import requests
import json
import util
log = util.Logger()

class Page(object):
    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

    def process(self):
        pass

class StaticItems(Page):
    _section = '[not implemented]'
    def process(self):
        log.debug('Fetching {0} page!'.format(self._section))

class Index(StaticItems):
    _section = 'index'

class Categories(StaticItems):
    _section = 'categories'

class AToO(Page):
    def process(self):
        log.debug('Fetching videos, A-Ö!')

class Videos(Page):
    def process(self):
        log.debug('Fetching a list of videos!')

class PlayVideo(Page):
    def process(self):
        log.debug('Playing video!')