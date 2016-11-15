import os

from setuptools import setup, find_packages
#from distutils.core import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [

    # ----------------------------------------------
    #   Environment
    # ----------------------------------------------
    'setuptools>=11.3',
    #'six>=1.5.2',


    # ----------------------------------------------
    #   Backend
    # ----------------------------------------------
    # pyramid core
    #'pyramid==1.5a2',
    'pyramid==1.4.2',
    'pyramid_debugtoolbar',
    'pyramid_mako',
    'Akhet==2.0',
    'waitress',
    'Paste==1.7.5.1',
    'PasteScript==1.7.5',

    # caching
    'Beaker==1.7.0dev',
    'pyramid_beaker==0.8',
    'pymongo==2.8',
    'mongodb_gridfs_beaker==0.5.4',

    # web services
    'cornice==0.15',

    # authorization
    'PyCrypto==2.6.1',
    'jws==0.1.2',
    'python_jwt==0.3.1',
    'pbkdf2==1.3',


    # ----------------------------------------------
    #   Infrastructure
    # ----------------------------------------------

    # HTTP
    'requests==2.5.1',
    'requests-oauthlib==0.4.0',
    'mechanize==0.2.5',

    # HTML
    'BeautifulSoup==3.2.1',

    # SNI support
    'pyOpenSSL==16.0.0',
    'pyasn1==0.1.9',
    'ndg-httpsclient==0.4.2',


    # ----------------------------------------------
    #   Business logic
    # ----------------------------------------------
    'Bunch==1.0.1',
    'ago==0.0.6',
    'pyparsing==2.0.2',
    'mongoengine==0.8.7',
    'blinker==1.3',
    'python-dateutil==2.2',
    'lxml==3.4.1',
    'openpyxl==2.1.0',
    'jsonpointer==1.6',
    'arrow==0.4.4',
    'transitions==0.2.4',
    'xlrd==0.9.3',
    'Jinja2==2.8',
    'validate_email==1.3',
    'pandas==0.18.1',
    'XlsxWriter==0.9.3',
    'html2text==2016.5.29',
    'envoy==0.0.3',

    # ----------------------------------------------
    #   user interface
    # ----------------------------------------------
    # fanstatic
    'fanstatic==1.0a2',
    'pyramid_fanstatic==0.4',

    # bootstrap
    'js.bootstrap==2.3.1',
    #'js.bootstrap==3.0.0.1',

    # jquery
    'js.jquery==1.9.1',
    'js.jquery_shorten==1.0.0a1',
    'js.purl==2.3.1a1',
    'js.select2==3.4.1',

    # jquerui
    #'js.jqueryui==1.10.3',
    #'js.jqueryui_bootstrap==0.0.0',

    # fontawesome
    'css.fontawesome==3.2.1',

    # marionette, backbone and prerequisites
    'js.marionette==1.1.0a2',
    'js.underscore_string==2.3.0a1',

]

test_requires = [
    # ----------------------------------------------
    #   testing
    # ----------------------------------------------
    'nose==1.3.3',
    'nose-exclude==0.2.0',
    'nose2-cov==1.0a4',
]

setup(name='elmyra.ip.access.epo',
      version='0.125.2',
      description='elmyra.ip.access.epo',
      long_description=README,
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
      #packages=['elmyra.ip.access.epo'],
      include_package_data=True,
      package_data={
          'elmyra.ip.access.epo': [
              'resources/*.*',
              'templates/*.mako',
              'static/js/**/*.js', 'static/js/**/*.map', 'static/js/**/*.swf', '**/**/*.css',
              '**/**/*.jpg', '**/**/*.gif', '**/**/*.svg', '**/**/**/*.svg',
              'static/widget/**/**/*.*',
          ],
          'elmyra.ip.util.render': ['*.js'],
      },
      zip_safe=False,
      test_suite='nose.collector',
      install_requires=requires,
      tests_require=test_requires,

      dependency_links=[
        'https://github.com/elmyra-org/js.marionette/tarball/1.1.0a2#egg=js.marionette-1.1.0a2',
      ],

      entry_points={
        'paste.app_factory': [
            'main = elmyra.ip.access.epo:main',
            ],
        'beaker.backends': [
            'mongodb = elmyra.ip.util.database.beaker_mongodb:MongoDBNamespaceManager',
            ],
        'console_scripts': [
            'navigator-clean-browser-db = elmyra.ip.navigator.commands:clean_browser_database',
            ],
        },

    )