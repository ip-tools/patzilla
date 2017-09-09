.. _install-production:

##################################
Install IP Navigator on production
##################################

YMMV.

***********
Application
***********

Prerequisites
-------------
Run once to prepare the sandbox environment for deployment tasks::

    make setup-maintenance

Cut a new release
-----------------
::

    # Possible increments: patch,minor,major
    make release bump=minor

Deploy application
------------------
From inside repository, with virtualenv activated.
::

    # Possible targets: develop,staging,prod
    make install target=develop

    # Optionally pin to a specific version
    make install target=develop version=0.30.0

Upload nginx-auth lua code::

    fab upload_nginx_auth


*********************
Application container
*********************

uWSGI configuration
-------------------
::

    mkdir /opt/elmyra/patentsearch/sites/patoffice

    cp /etc/uwsgi/apps-available/patentsearch-staging.ini /etc/uwsgi/apps-available/patentsearch.patoffice.ini
    # edit new file to match new site
    [uwsgi]
    uid = www-data
    gid = www-data
    virtualenv = /opt/elmyra/patentsearch/sites/patoffice/.venv27
    paste = config:/opt/elmyra/patentsearch/sites/patoffice/production.ini

    ln -s /etc/uwsgi/apps-available/patentsearch.patoffice.ini /etc/uwsgi/apps-enabled/

    service uwsgi restart patentsearch.patoffice


**********
Web server
**********

SSL certificates
----------------
::

    cd /etc/pki/tls/certs
    make patentsearch-staging.elmyra.de.csr
    cat patentsearch-staging.elmyra.de.csr

    https://www.startssl.com/

    echo {output} > patentsearch-staging.elmyra.de.crt

    make bundle CRT=patentsearch-staging.elmyra.de.crt
    make ocsp CRT=patentsearch-staging.elmyra.de.bundle.crt

    ln -s /etc/pki/tls/certs/patentsearch.patoffice.elmyra.de.bundle.crt /etc/nginx/ssl/
    ln -s /etc/pki/tls/certs/patentsearch.patoffice.elmyra.de.key /etc/nginx/ssl/


Nginx configuration
-------------------
::

    cp /etc/nginx/sites-available/patentsearch-staging.elmyra.de /etc/nginx/sites-available/patentsearch.patoffice.elmyra.de
    # edit new file to match new site

    ln -s /etc/nginx/sites-available/patentsearch.patoffice.elmyra.de /etc/nginx/sites-enabled/patentsearch.patoffice.elmyra.de

    service nginx reload



******************
External utilities
******************

gif2tiff
--------

    apt-get install libtiff-tools


PhantomJS
---------
::

    wget https://bitbucket.org/ariya/phantomjs/downloads/phantomjs-1.9.7-linux-x86_64.tar.bz2
    cp phantomjs-1.9.7-linux-x86_64/bin/phantomjs /usr/local/bin/


Fonts
-----
https://gist.github.com/madrobby/5489174

::

    apt-get install fontconfig libfontconfig libfreetype6 ttf-xfree86-nonfree ttf-mscorefonts-installer

    wget --no-check-certificate https://gist.github.com/madrobby/5265845/raw/edd7ba1f133067afd2bd60ba7d40e684bb852c6c/localfonts.conf
    mv localfonts.conf /etc/fonts/local.conf

