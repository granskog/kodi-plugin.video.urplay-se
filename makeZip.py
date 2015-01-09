# -*- coding: utf-8 -*-
import sys
import os
import xml.etree.ElementTree as ET
import zipfile
import __main__
_thisFile = __main__.__file__

try:
    tree = ET.parse('addon.xml')
except IOError:
    sys.exit('Unable to open addon.xml.')
except ET.ParseError:
    sys.exit('Invalid file format.')

_root = tree.getroot()
if _root is not None:
    try:
        _version = _root.attrib['version']
        _id = _root.attrib['id']
    except KeyError:
        sys.exit("Unable to find 'version' and 'plugin id' in addon.xml.")

zfName = '{}-{}.zip'.format(_id, _version)
zippy = zipfile.ZipFile(zfName, 'w',  zipfile.ZIP_DEFLATED)

_excludes = set([_thisFile, zfName])
for root, dirs, files in os.walk('.', topdown = True):
    files = [f for f in files if not f.startswith('.') and f not in _excludes]
    dirs[:] = [d for d in dirs if not d.startswith('.')]
    for f in files:
        if f.endswith(('.pyo', '.pyc')):
            continue
        path = os.path.join(_id, os.path.relpath((os.path.join(root, f))))
        print 'Writing "{}" to zippy with path: '.format(f), path
        zippy.write(os.path.join(root, f), path)

zippy.close()
print '''\o/
 | Done!
 ^'''