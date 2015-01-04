# -*- coding: utf-8 -*-
import xbmcgui
import xbmcplugin
import requests
import json
import urllib
import util
from parsedom import parseDOM

log = util.Logger()

class BaseHandler(object):
    @property
    def URL(self):
        return 'http://urplay.se'

    def __init__(self, plugin):
        self._plugin = plugin

    def process(self):
        pass

class StaticItems(BaseHandler):
    _items = []
    def process(self):
        log.debug('Fetching {0} page!'.format(type(self).__name__))
        
        localize = self._plugin.localize
        for langCode, uri in self._items:
            url = self._plugin.baseURL + uri
            li = xbmcgui.ListItem(localize(langCode), iconImage='DefaultFolder.png')
            xbmcplugin.addDirectoryItem(handle = self._plugin.handle, url = url,
                listitem = li, isFolder = True)

        xbmcplugin.endOfDirectory(self._plugin.handle)

class Index(StaticItems):
    _items = [
        # (30100, '/startsida'),
        (30101, '/kategori/Mest-spelade'),
        (30102, '/kategori/Mest-delade'),
        (30103, '/kategori/Senaste'),
        (30104, '/kategori/Sista-chansen'),
        (30105, '/kategori'),
        (30106, '/aktuellt'),
        (30107, '/a-to-o')
    ]

class Categories(StaticItems):
    _items = [
        (30200, '/kategori/Dokumentar'),
        (30201, '/kategori/Forelasningar-debatt'),
        (30202, '/kategori/Vetenskap'),
        (30203, '/kategori/Kultur-historia'),
        (30204, '/kategori/Samhalle'),
        (30205, '/kategori/Sprak'),
        (30206, '/kategori/Barn')
    ]

class AToO(StaticItems):
    _items = [
        (30100, '/')
    ]

class Current(StaticItems):
    _items = [
        (30100, '/')
    ]

class Videos(BaseHandler):
    def process(self, page):
        log.debug('Fetching a list of videos on "{0}" page!'.format(page))

class PlayVideo(BaseHandler):
    @property
    def URL(self):
        return super(PlayVideo, self).URL + '/Produkter/'

    def process(self, id):
        try:
            url = self.URL + id
            log.info('Fetching video info from "{0}".'.format(url))
            req = requests.get(url)
            req.raise_for_status()

            match = re.search(r'urPlayer\.init\((.*?)\);', req.text)
            if match is None:
                raise Exception('No JSON data found')

            js = json.loads(match.group(1))
            fl = js['file_hd'] if j['file_hd'] != '' else j['file_flash']
            vidURL = 'http://{streaming_config[streamer][redirect]}/'\
                    'urplay/_definst_/mp4:{vid_file}/'\
                    '{streaming_config[http_streaming][hls_file]}'.format(vid_file = fl, **js)

            li = xbmcgui.ListItem(name = id, path = vidURL)
            log.debug('Playing video from URL: "{0}"'.format(vidURL))
            # xbmcplugin.setResolvedUrl(self._plugin.handle, True, li)

            # TODO: Subtitles!

        except Exception as e:
            xbmcplugin.setResolvedUrl(self._plugin.handle, False, None)
            log.error('Unable to fetch video info from url "{0}" ({1}).'.format(url, e))