# -*- coding: utf-8 -*-
# (c) 2013 Andreas Motl, Elmyra UG
import os
from distutils.core import run_setup
from fabric.decorators import task, hosts
from fabric.colors import yellow
from cuisine import run
from pip.util import ask

@task
@hosts('root@almera.elmyra.de')
def install(version):

    current_dir = os.path.dirname(__file__)
    project_path = os.path.join(current_dir, 'elmyra.ip.access.epo')
    pkg_version = setuptools_get_version(project_path)
    pkg_name = setuptools_get_name(project_path)

    if not version:
        version = pkg_version

    print 'Installing package ' + yellow(pkg_name) + ', version ' + yellow(version)
    #response = ask('Proceed (y/n)? ', ('y', 'n'))
    response = 'y'

    if response == 'y':

        #--index-url=http://c.pypi.python.org/simple
        pip_cmd = 'source /opt/ops-chooser/.venv27/bin/activate; sh -c "pip install --download-cache=/var/cache/pip --verbose {options} {requirement}"'

        #run(pip_cmd.format(requirement='which', options=''))
        #run(pip_cmd.format(requirement='/root/install/ops-chooser/js.*', options=''))
        run(pip_cmd.format(requirement='/root/install/ops-chooser/elmyra.ip.access.epo-{version}.tar.gz'.format(version=version), options=''))


def setuptools_get_version(project_path):
    setup_script = os.path.join(project_path, 'setup.py')
    # stop_after=('init', 'config', 'commandline', 'run')
    distribution_info = run_setup(setup_script, stop_after="commandline")
    return distribution_info.get_version()

def setuptools_get_name(project_path):
    setup_script = os.path.join(project_path, 'setup.py')
    # stop_after=('init', 'config', 'commandline', 'run')
    distribution_info = run_setup(setup_script, stop_after="commandline")
    return distribution_info.get_name()
