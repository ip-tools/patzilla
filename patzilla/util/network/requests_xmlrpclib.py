# -*- coding: utf-8 -*-
"""
A replacement transport for Python xmlrpc library.
https://gist.github.com/chrisguitarguy/2354951
https://github.com/astraw/stdeb/blob/master/stdeb/transport.py

Usage:

    >>> import xmlrpclib
    >>> #from transport import RequestsTransport
    >>> s = xmlrpclib.ServerProxy('http://yoursite.com/xmlrpc', transport=RequestsTransport())
    >>> #s.demo.sayHello()
    Hello!
"""
try:
    import xmlrpc.client as xmlrpc
except ImportError:
    import xmlrpc.client as xmlrpc

import requests

class RequestsTransport(xmlrpc.Transport):
    """
    Drop in Transport for xmlrpclib that uses Requests instead of httplib
    """
    # change our user agent to reflect Requests
    user_agent = "Python XMLRPC with Requests (python-requests.org)"

    # override this if you'd like to https
    use_https = False

    def __init__(self, *args, **kwargs):
        self.session = None
        self.timeout = None
        if 'session' in kwargs:
            self.session = kwargs['session']
            del kwargs['session']
        if 'timeout' in kwargs:
            self.timeout = kwargs['timeout']
            del kwargs['timeout']
        return xmlrpc.Transport.__init__(self, *args, **kwargs)

    def request(self, host, handler, request_body, verbose):
        """
        Make an xmlrpc request.
        """
        client = self.session or requests
        headers = {'User-Agent': self.user_agent,
                   'Content-Type': 'text/xml',
                   }
        url = self._build_url(host, handler)
        try:
            resp = client.post(url, data=request_body, headers=headers, timeout=self.timeout)
        except ValueError:
            raise
        except Exception:
            raise # something went wrong
        else:
            try:
                resp.raise_for_status()
            except requests.RequestException as e:
                raise xmlrpc.ProtocolError(url, resp.status_code,
                    str(e), resp.headers)
            else:
                return self.parse_response(resp)

    def parse_response(self, resp):
        """
        Parse the xmlrpc response.
        """
        p, u = self.getparser()
        p.feed(resp.text)
        p.close()
        return u.close()

    def _build_url(self, host, handler):
        """
        Build a url for our request based on the host, handler and use_http
        property
        """
        scheme = 'https' if self.use_https else 'http'
        return '%s://%s/%s' % (scheme, host, handler)
        #return '%s://%s%s' % (scheme, host, handler)

