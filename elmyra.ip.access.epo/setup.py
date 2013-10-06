import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.txt')).read()
CHANGES = open(os.path.join(here, 'CHANGES.txt')).read()

requires = [

    # foundation: pyramid
    'pyramid==1.5a2',
    'Akhet==2.0',
    'pyramid_debugtoolbar',
    'waitress',
    'pyramid_mako',

    # frontend
    'fanstatic==1.0a2',
    'pyramid_fanstatic==0.4',

    # bootstrap
    'js.bootstrap==2.3.1',
    #'js.bootstrap==3.0.0.1',

    # jquery and jquerui
    'js.jquery==1.9.1',
    'js.jqueryui==1.10.3',
    'js.jqueryui_bootstrap==0.0.0',

    # fontawesome
    'css.fontawesome==3.2.1',

setup(name='elmyra.ip.access.epo',
      version='0.0.0',
      description='elmyra.ip.access.epo',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='elmyra.ip.access.epo',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = elmyra.ip.access.epo:main
      """,
      )
