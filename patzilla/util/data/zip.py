# -*- coding: utf-8 -*-
# (c) 2015-2016 Andreas Motl, Elmyra UG
import os
import time
import json
import tempfile
import zipfile

def zip_multi(multi):

    # use temporary file as zipfile
    tmpfh, tmppath = tempfile.mkstemp()
    os.close(tmpfh)

    # create zip
    zip = zipfile.ZipFile(tmppath, "w")
    now = time.localtime(time.time())[:6]

    # http://stackoverflow.com/questions/434641/how-do-i-set-permissions-attributes-on-a-file-in-a-zip-file-using-pythons-zip/434689#434689
    unix_permissions = 0644 << 16L

    # add index file for drawings
    """
    index_payload = json.dumps({'type': 'drawings', 'filenames': filenames_full})
    info = zipfile.ZipInfo(number + '.drawings.json')
    info.date_time = now
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = unix_permissions
    zip.writestr(info, index_payload)
    """

    # add report file
    info = zipfile.ZipInfo('@report.json')
    info.date_time = now
    info.compress_type = zipfile.ZIP_STORED
    info.external_attr = unix_permissions
    zip.writestr(info, json.dumps(multi['report'], indent=4))

    # add files
    for entry in multi['results']:
        payload = entry['payload']
        filename = entry['filename']
        info = zipfile.ZipInfo(filename)
        info.date_time = now
        info.compress_type = zipfile.ZIP_STORED
        info.external_attr = unix_permissions
        zip.writestr(info, payload)

    zip.close()

    # read zip
    fh = open(tmppath, 'rb')
    payload_zipped = fh.read()
    fh.close()

    # destroy zip
    os.unlink(tmppath)

    return payload_zipped
