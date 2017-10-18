.. _mongodb-backup:

##############
MongoDB backup
##############

backupninja_ is a good choice for making daily backups.
The addon `backupninja-mongodb`_ helps with MongoDB_.
YMMV.

Setup backupninja
-----------------
::

    apt install backupninja

Edit configuration file /etc/backupninja.conf.


Setup backup handler for MongoDB
--------------------------------
::

    mkdir ~/install
    cd ~/install
    wget --no-check-certificate https://raw.githubusercontent.com/osinka/backupninja-mongodb/master/mongodb
    wget --no-check-certificate https://raw.githubusercontent.com/osinka/backupninja-mongodb/master/mongodb.helper

    mv mongodb* /usr/share/backupninja/

Configure /etc/backup.d/30.mongodb::

    dbhost  = localhost
    dbport  = 27017
    mongodb = patzilla

    # dbhost    = <database hostname>
    # dbport    = <database port>
    # mongouser = <username>
    # mongopass = <password>
    # mongodb   = <db to backup>
    # mongocollection = <collection to backup>

Care for appropriate permissions::

    chmod go-rwx /etc/backup.d/30.mongodb

Test
----
::

    backupninja --test --now
    backupninja --debug --now

