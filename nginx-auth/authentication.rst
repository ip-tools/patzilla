Anonymous access denied
-----------------------
curl -i localhost:6544/auth::

    HTTP/1.1 401 Unauthorized
    Server: ngx_openresty/1.2.7.6
    Date: Fri, 11 Jul 2014 21:45:11 GMT
    Content-Type: text/plain
    Transfer-Encoding: chunked
    Connection: keep-alive
    www-authenticate: Basic realm=""

    401 Access Denied


Authentication successful
-------------------------
curl -i --basic --user 123:456 localhost:6544/auth::

    HTTP/1.1 200 OK
    Server: ngx_openresty/1.2.7.6
    Date: Fri, 11 Jul 2014 23:01:20 GMT
    Content-Type: text/html
    Transfer-Encoding: chunked
    Connection: keep-alive
    Set-Cookie: Auth=1405123280:NTBlZGRjODkwYjFhMTEwMDJiNjBiNTJjZTdjZWMxYzdmYzg4YzljZQ==; Path=/; Domain=; Expires=Sat, 12-Jul-14 00:01:20 GMT; ; Max-Age=3600; HttpOnly

    <html><head><script>location.reload()</script></head></html>


Authentication failed
---------------------
curl -i --basic --user abc:def localhost:6544/auth::

    HTTP/1.1 401 Unauthorized
    Server: ngx_openresty/1.2.7.6
    Date: Fri, 11 Jul 2014 23:03:02 GMT
    Content-Type: text/plain
    Transfer-Encoding: chunked
    Connection: keep-alive
    www-authenticate: Basic realm=""

    401 Access Denied


Authenticated access successful
-------------------------------
curl -i --cookie 'Auth=1405124337:YTNjODQ0MmUwMmI1OWFmMzBjNjY2ODFkZDdkOWQyYWVlNWRjNTU3Nw==' localhost:6544/abc::

    HTTP/1.1 200 OK
    ...
