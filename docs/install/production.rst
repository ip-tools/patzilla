.. include:: ../resources.rst

.. _install-production:

################
Production setup
################
For getting an idea about how to install PatZilla in a production environment.
The following documentation is for Debian GNU/Linux 8 (jessie).
The designated target directory is ``/opt/patzilla``.


**************
Infrastructure
**************
Foundation infrastructure::

    apt install nginx-extras lua-cjson uwsgi uwsgi-plugin-python


***********
Application
***********

Prerequisites
=============
Run once to prepare the sandbox environment for deployment tasks::

    pip install --requirement requirements-deploy.txt

Deploy application
==================
::

    # Define target host for installing package
    export PATZILLA_HOST=root@appserver.example.org

    # Possible targets: develop,staging,prod
    make install target=patzilla-develop

    # Optionally nail to a specific version
    make install target=patzilla-develop version=0.30.0

Upload nginx-auth lua code::

    make install-nginx-auth


*********************
Application container
*********************

Prerequisites
=============

System configuration
====================
/etc/sysctl.conf::

    # The maximum number of "backlogged sockets".  Default is 128.
    net.core.somaxconn = 2048

Reload configuration::

    sysctl -p


Application configuration
=========================
::

    cp /opt/patzilla/sites/patzilla-develop/production.ini.tpl /opt/patzilla/sites/patzilla-develop/production.ini

Edit ``production.ini`` according to your needs.


uWSGI configuration
===================
/etc/uwsgi/apps-available/patzilla-develop.ini::

    [uwsgi]
    uid = www-data
    gid = www-data
    processes = 8
    listen = 2048
    buffer-size = 32768

    plugins = python
    virtualenv = /opt/patzilla/sites/patzilla-develop/.venv27
    paste = config:/opt/patzilla/sites/patzilla-develop/production.ini

    paste-logger = true
    #sync-log = true

Activate::

    ln -s /etc/uwsgi/apps-available/patzilla-develop.ini /etc/uwsgi/apps-enabled/

Start::

    service uwsgi restart patzilla-develop

Watch::

    tail -F /var/log/uwsgi/app/patzilla-develop.log


**********
Web server
**********

Nginx configuration
===================
/etc/nginx/snippets/ssl-best-practice.conf::

    # Contemporary SSL security settings
    # https://juliansimioni.com/blog/https-on-nginx-from-zero-to-a-plus-part-2-configuration-ciphersuites-and-performance/
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    #ssl_protocols TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers on;
    ssl_ciphers 'kEECDH+ECDSA+AES128 kEECDH+ECDSA+AES256 kEECDH+AES128 kEECDH+AES256 kEDH+AES128 kEDH+AES256 DES-CBC3-SHA +SHA !aNULL !eNULL !LOW !kECDH !DSS !MD5 !EXP !PSK$

    # Diffie-Hellman parameter for DHE ciphersuites, recommended 2048 bits
    #ssl_dhparam /etc/nginx/ssl/dhparam.pem;
    ssl_dhparam /etc/nginx/ssl/dhparam-4096.pem;

    add_header Strict-Transport-Security 'max-age=31536000';
    ssl_stapling on;

    # enable session resumption to improve https performance
    # http://vincent.bernat.im/en/blog/2011-ssl-session-reuse-rfc5077.html
    ssl_session_cache builtin:1000 shared:SSL:20m;
    ssl_session_timeout 5m;

    location /.well-known {
        alias /srv/www/default/htdocs/.well-known;
    }

/etc/nginx/conf.d/nginx-auth.conf::

    # Configure Lua package search path
    lua_package_path ";;/opt/patzilla/nginx-auth/lua/?.lua;";

    # Uncomment this for working on the Lua code
    #lua_code_cache off;

/etc/nginx/snippets/patzilla/container.conf::

    set $luadir "/opt/patzilla/nginx-auth/lua";

    listen 80;
    listen 443 ssl;
    #listen 443 ssl spdy;

    include snippets/ssl-best-practice.conf;

    # individual nginx logs for this vhost
    access_log  /var/log/nginx/$host-access.log;

    root /srv/www/null;

    # http://stackoverflow.com/questions/389456/cookie-blocked-not-saved-in-iframe-in-internet-explorer
    more_set_headers 'P3P: CP="This site does not have a p3p policy."';

    location = "/auth" {
        lua_need_request_body on;
        content_by_lua_file "$luadir/authentication.lua";
    }

/etc/nginx/snippets/patzilla/application.conf::

    # webapp via uwsgi
    uwsgi_read_timeout 1500;


    # userid gets set by access.lua
    set $user_id "";

    access_by_lua_file "$luadir/access.lua";

    include       uwsgi_params;
    uwsgi_param   SCRIPT_NAME                 '';
    uwsgi_param   REQUEST_METHOD              $echo_request_method;

    # propagate userid to upstream service via http request headers
    uwsgi_param   HTTP_X_USER_ID              $user_id;

    # http://docs.pylonsproject.org/projects/waitress/en/latest/#using-behind-a-reverse-proxy
    # https://wiki.apache.org/couchdb/Nginx_As_a_Reverse_Proxy
    uwsgi_param   HTTP_X_REAL_IP              $remote_addr;
    uwsgi_param   HTTP_X_FORWARDED_PROTO      $scheme;
    uwsgi_param   HTTP_X_FORWARDED_FOR        $proxy_add_x_forwarded_for;


    #add_header    Content-Security-Policy  "default-src https:; script-src https: 'unsafe-inline' 'unsafe-eval'; style-src https: 'unsafe-inline'";
    #add_header    Content-Security-Policy  "script-src 'unsafe-inline' 'unsafe-eval'; style-src https: 'unsafe-inline'";
    # config to enable HSTS(HTTP Strict Transport Security) https://developer.mozilla.org/en-US/docs/Security/HTTP_Strict_Transport_Security
    # to avoid ssl stripping https://en.wikipedia.org/wiki/SSL_stripping#SSL_stripping
    add_header Strict-Transport-Security "max-age=31536000; includeSubdomains";

    if ($server_port = 80) {
        #rewrite ^ https://$host$request_uri;
        rewrite (.*) https://$http_host$1;
    }

    # pass-through static and api urls
    rewrite ^/static/(.*)$ /static/$1 break;
    rewrite ^/api/(.*) /api/$1 break;

    # rewrite urls to match application
    rewrite ^/(.+)$ /navigator/$1 break;
    rewrite ^/?(.*)$ /navigator/$1 break;


/etc/nginx/sites-available/patzilla-develop.example.org::

    # webapp via uwsgi
    upstream patzilla-develop {
        server unix:/run/uwsgi/app/patzilla-develop/socket;
    }

    server {

      server_name patzilla-develop.example.org;

      include snippets/patzilla/container.conf;

      # SSL: Self-signed
      include snippets/snakeoil.conf;

      # SSL: Let's Encrypt
      #ssl_certificate /etc/letsencrypt/live/patzilla-develop.example.org/fullchain.pem;
      #ssl_certificate_key /etc/letsencrypt/live/patzilla-develop.example.org/privkey.pem;

      error_log   /var/log/nginx/patzilla-develop.example.org-error.log info;

      location / {

        # webapp via uwsgi
        uwsgi_pass        patzilla-develop;

        include snippets/patzilla/application.conf;

      }

    }


Activate::

    ln -s /etc/nginx/sites-available/patzilla-develop.example.org /etc/nginx/sites-enabled/patzilla-develop.example.org

Test and reload::

    nginx -t
    service nginx reload

Watch::

    tail -F /var/log/nginx/patzilla-develop.example.org-*.log


SSL certificates
================
::

    certbot certonly --webroot-path /srv/www/default/htdocs --domains patzilla-develop.example.org --expand



******************
External utilities
******************

ImageMagick
===========

Introduction
------------
We found on some systems the ``convert`` tool from ImageMagick 6 yields drawings with
low quality (contrast, etc.), so you might want to consider installing ImageMagick >= 7.
The software will search for appropriate candidates in this order::

    candidates = [
        '/opt/imagemagick-7.0.2/bin/convert',
        '/opt/imagemagick/bin/convert',
        '/opt/local/bin/convert',
        '/usr/bin/convert',
    ]

Setup
-----
::

    wget http://www.imagemagick.org/download/ImageMagick.tar.gz
    ./configure --prefix=/opt/imagemagick
    make && make install

::

    /opt/imagemagick/bin/convert --version
    Version: ImageMagick 7.0.2-6 Q16 x86_64 2016-08-06 http://www.imagemagick.org


PDFtk
=====

Introduction
------------
We definitively want PDFtk_ >= 2 for joining PDF documents.
The software will search for appropriate candidates in this order::

    candidates = [
        '/opt/pdflabs/pdftk/bin/pdftk',
        '/usr/local/bin/pdftk',
        '/usr/bin/pdftk',
    ]

Setup
-----
::

    apt install pdftk

::

    pdftk --version
    pdftk 2.02 a Handy Tool for Manipulating PDF Documents

On systems with older PDFtk releases::

    wget http://www.pdflabs.com/tools/pdftk-the-pdf-toolkit/pdftk-2.02-src.zip
    make -f Makefile.Debian
    make -f Makefile.Debian install

unoconv
=======
unoconv_ is used to convert spreadsheet worksheets to PDF documents.
::

    # Debian Linux
    apt install unoconv libreoffice


***********
Maintenance
***********
PatZilla is almost maintenance-free. However, there are a few things to take into consideration.


Database backup
===============
Please refer to :ref:`mongodb-backup` about how to make
daily backups of the production database.


Database frontend
=================
You might want to have a look at Genghis_ for a user interface to MongoDB_.
Please follow up at :ref:`genghis` about setup instructions.


Document and query cache
========================
PatZilla caches all responses in the databases with various TTLs
to provide a better user experience. If this cache fills up too
much, you might want to purge it from time to time::

    mongo beaker --eval 'db.dropDatabase();'

You might want to restart the application after that,
better safe than sorry.


----

***************************************
External utilities - currently not used
***************************************
These tools are currently not used, but references are kept for future reactivation.


PhantomJS
=========
PhantomJS_ is a headless WebKit scriptable with a JavaScript API. It has fast and native support
for various web standards: DOM handling, CSS selector, JSON, Canvas, and SVG.

It is used for rendering PDF documents from HTML.
::

    apt install phantomjs

    # Deprecated
    #wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.7-linux-x86_64.tar.bz2
    #cp phantomjs-1.9.7-linux-x86_64/bin/phantomjs /usr/local/bin/


Fonts
-----
Tweak PhantomJS for better rendering quality.
https://gist.github.com/madrobby/5489174

::

    apt install fontconfig libfontconfig libfreetype6 ttf-xfree86-nonfree ttf-mscorefonts-installer

    wget --no-check-certificate https://gist.github.com/madrobby/5265845/raw/edd7ba1f133067afd2bd60ba7d40e684bb852c6c/localfonts.conf
    mv localfonts.conf /etc/fonts/local.conf


gif2tiff
========
Convert drawings in GIF format from CIPO.
::

    apt install libtiff-tools

