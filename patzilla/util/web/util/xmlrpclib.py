# -*- coding: utf-8 -*-
# (c) 2014-2015 Andreas Motl, Elmyra UG
from __future__ import absolute_import
import sys
import socket
import xmlrpclib
import ssl

# https://stackoverflow.com/questions/372365/set-timeout-for-xmlrpclib-serverproxy/14397619#14397619
class XmlRpcTimeoutServer:

    def __init__(self, url, timeout=None):
        self.__url = url
        self.__timeout = timeout
        self.__prevDefaultTimeout = None

        # PEP 476: verify HTTPS certificates by default (implemented from Python 2.7.9)
        # https://bugs.python.org/issue22417
        if sys.hexversion >= 0x02070900:
            ssl._create_default_https_context = ssl._create_unverified_context

    def __enter__(self):
        try:
            if self.__timeout:
                self.__prevDefaultTimeout = socket.getdefaulttimeout()
                socket.setdefaulttimeout(self.__timeout)
            proxy = xmlrpclib.Server(self.__url, allow_none=True)

        except Exception as ex:
            raise Exception("Unable create XMLRPC-proxy for url '%s': %s" % (self.__url, ex))

        return proxy

    def __exit__(self, type, value, traceback):
        if self.__prevDefaultTimeout is None:
            socket.setdefaulttimeout(self.__prevDefaultTimeout)
