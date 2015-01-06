# -*- coding: utf-8 -*-
import xbmcgui
import xbmcplugin
import requests
import json

from util import Logger, URL, URLBuilder
from parsedom import parseDOM

log = Logger()

class BaseHandler(object):
    __metaclass__ = URLBuilder
    url = URL('http://urplay.se')
    _html = None

    def __init__(self, plugin):
        self._plugin = plugin

    @property
    def html(self):
        if not self._html:
            log.info('Fetching html page "{0}".'.format(self.url))
            # self._response = requests.get(self.url())
            # self._response.raise_for_status()
            # self._html = self._response.text
        return self._html

    def process(self):
        pass

class Collection(BaseHandler):
    def _fetch(self):
        return []

    def process(self):
        items = self._fetch()
        # Unfortunately addDirectoryItems() does not work with generators.
        # Call list() on the generator object.
        xbmcplugin.addDirectoryItems(self._plugin.handle, list(items))
        xbmcplugin.endOfDirectory(self._plugin.handle)

class StaticDir(Collection):
    _items = []
    def _fetch(self):
        log.debug('Printing the {0} page.'.format(type(self).__name__))
        for langCode, path in self._items:
            url = self._plugin.baseURL + path
            li = xbmcgui.ListItem(self._plugin.localize(langCode),
                iconImage='DefaultFolder.png')
            yield url, li, True

class Index(StaticDir):
    _items = [
        # (30100, '/startsida'),
        (30101, '/category/Mest-spelade'),
        (30102, '/category/Mest-delade'),
        (30103, '/category/Senaste'),
        (30104, '/category/Sista-chansen'),
        (30105, '/category'),
        (30106, '/current'),
        (30107, '/programmes')
    ]

class Categories(StaticDir):
    _items = [
        (30200, '/category/Dokumentar'),
        (30201, '/category/Forelasningar-debatt'),
        (30202, '/category/Vetenskap'),
        (30203, '/category/Kultur-historia'),
        (30204, '/category/Samhalle'),
        (30205, '/category/Sprak'),
        (30206, '/category/Barn')
    ]

class ProgrammesAToZ(StaticDir):
    _items = [
        (30100, '/')
    ]

class CurrentShows(StaticDir):
    _items = [
        (30100, '/')
    ]

class VideoCollection(Collection):
    url = URL('/', product_type = 'programtv')
    def __init__(self, plugin, path):
        super(VideoCollection, self).__init__(plugin)
        self.url.extend(path)

    def _fetch(self):
        text = self.html
        return []

class CurrentVideos(VideoCollection):
    url = URL('/Aktuellt/')

class Series(VideoCollection):
    url = URL('/Produkter/')

class Video(BaseHandler):
    url = URL('/Produkter/')
    def __init__(self, plugin, id):
        super(Video, self).__init__(plugin)
        self._id = id
        self.url.extend(id)

    def process(self):
        try:
            match = re.search(r'urPlayer\.init\((.*?)\);', self.html)
            if match is None:
                raise ValueError('No JSON data found')

            js = json.loads(match.group(1))
            fl = js['file_hd'] if js['file_hd'] != '' else js['file_flash']
            vidURL = 'http://{streaming_config[streamer][redirect]}/'\
                    'urplay/_definst_/mp4:{vid_file}/'\
                    '{streaming_config[http_streaming][hls_file]}'.format(vid_file = fl, **js)

            li = xbmcgui.ListItem(name = self._id, path = vidURL)
            log.debug('Playing video from URL: "{0}"'.format(vidURL))
            xbmcplugin.setResolvedUrl(self._plugin.handle, True, li)

            # TODO: Subtitles!

        except Exception as e:
            xbmcplugin.setResolvedUrl(self._plugin.handle, False, None)
            log.error('Unable to fetch video info from url "{0}" ({1}).'.format(self.url, e))
            raise