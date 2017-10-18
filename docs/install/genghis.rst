.. include:: ../resources.rst

.. _genghis:

#############
Genghis setup
#############

You might want to have a look at Genghis_ for a user interface to MongoDB_. YMMV.


Setup
-----
Let's use the `Ruby Version Manager (RVM)`_ for setting up Genghis_ isolated from the system Ruby.
::

    gpg2 --recv-keys 409B6B1796C275462A1703113804BB82D39DC0E3
    curl -L https://get.rvm.io | bash -s stable

Create separate user for running Genghis::

    useradd --groups rvm --home-dir /opt/genghis --create-home --shell /bin/bash genghis

Satisfy system dependencies::

    apt install apache2-utils libgmp-dev

Setup the application in the context of user "genghis"::

    su - genghis

    # https://stackoverflow.com/questions/16563115/how-to-install-rvm-system-requirements-without-giving-sudo-access-for-rvm-user/17219765#17219765
    rvm autolibs disable
    rvm list remote

    rvm install 2.3.3
    rvm use 2.3.3

    rvm gemset create genghis
    rvm gemset use genghis

    gem install genghisapp bson_ext

Run Genghis
-----------
::

    su - genghis
    rvm gemset use genghis
    genghisapp --host 127.0.0.1 --port 4444


Stop Genghis
------------
::

    su - genghis
    rvm gemset use genghis
    genghisapp --kill


Nginx mount
-----------
/etc/nginx/sites-available/mongodb-patzilla.example.org.conf::

    upstream genghis {
      server localhost:4444;
    }

    server {
        listen 80;
        listen 443;
        server_name mongodb-patzilla.example.org;

        root /srv/www/null;

        if ($server_port = 80) {
            rewrite (.*) https://$http_host$1;
        }

        ssl on;
        include snippets/ssl-best-practice.conf;

        # SSL: Self-signed
        include snippets/snakeoil.conf;

        # Let's Encrypt
        #ssl_certificate /etc/letsencrypt/live/mongodb-patzilla.example.org/fullchain.pem;
        #ssl_certificate_key /etc/letsencrypt/live/mongodb-patzilla.example.org/privkey.pem;

        location / {

            auth_basic            "Restricted";
            auth_basic_user_file  /opt/genghis/credentials;

            proxy_set_header   Host              $http_host;
            proxy_set_header   X-Real-IP         $remote_addr;
            proxy_set_header   X-Forwarded-Proto $scheme;
            add_header         Front-End-Https   on;

            proxy_pass http://genghis;

        }

    }

Create credentials::

    htpasswd -c /opt/genghis/credentials acme

Activate configuration::

    /etc/nginx/sites-available/mongodb-patzilla.example.org.conf /etc/nginx/sites-enabled/
    nginx -t
    systemctl reload nginx

