# -*- coding: utf-8 -*-
# (c) 2013 Andreas Motl, Elmyra UG
from fabric.decorators import task, hosts
from cuisine import run

@task
@hosts('root@almera.elmyra.de')
def install():

    #--index-url=http://c.pypi.python.org/simple
    pip_install = 'source /opt/ops-chooser/.venv/bin/activate; sh -c "pip install --download-cache=/var/cache/pip --verbose {options} {requirement}"'

    run(pip_install.format(requirement='which', options=''))
    run(pip_install.format(requirement='/root/install/ops-chooser/js.*', options=''))
    run(pip_install.format(requirement='/root/install/ops-chooser/elmyra.ip.access.epo*', options=''))
