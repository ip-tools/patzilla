import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
#CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [

    # ----------------------------------------------
    #   Environment
    # ----------------------------------------------
    'setuptools>=36.4.0',       # 36.6.0
    'six>=1.10.0',              # 1.11.0


    # ----------------------------------------------
    #   Backend
    # ----------------------------------------------

    # Pyramid core
    'pyramid==1.9.1',
    'pyramid_debugtoolbar==4.3',
    'Pygments==2.2.0',
    'pyramid_mako==1.0.2',
    'Jinja2==2.9.6',
    'Akhet==2.0',
    'waitress==1.1.0',
    'Paste==2.0.3',
    'PasteScript==2.0.2',

    # Caching
    'Beaker==1.9.0',
    'pyramid_beaker==0.8',

    # Can't upgrade to pymongo-3.5.1 due to "from pymongo.connection import Connection" usage in "mongodb_gridfs_beaker" module.
    'pymongo==2.9.5',           # 3.5.1
    'mongodb_gridfs_beaker==0.5.4',

    # web services
    'cornice==2.4.0',           # 2.4.1

    # authorization
    'pycrypto==2.6.1',
    'jws==0.1.3',
    'python_jwt==2.0.2',        # 3.0.0
    'pbkdf2==1.3',


    # ----------------------------------------------
    #   Infrastructure
    # ----------------------------------------------

    # HTTP
    'requests==2.18.4',
    'requests-oauthlib==0.8.0',
    'mechanize==0.3.5',         # 0.3.6

    # HTML
    'BeautifulSoup==3.2.1',     # beautifulsoup4==4.6.0

    # SNI support
    'pyOpenSSL==17.3.0',
    'cryptography==2.0.3',      # 2.1.2
    'pyasn1==0.3.7',
    'ndg-httpsclient==0.4.3',


    # ----------------------------------------------
    #   Console interface
    # ----------------------------------------------
    'docopt==0.6.2',


    # ----------------------------------------------
    #   Business logic
    # ----------------------------------------------
    'Bunch==1.0.1',
    'ago==0.0.9',
    'pyparsing==2.0.2',         # 2.2.0
    'mongoengine==0.13.0',      # 0.14.3
    'blinker==1.4',
    'python-dateutil==2.6.1',
    # Remark: Both lxml 3.8.0 and 4.0.0 will segfault on Debian Wheezy (7.11)
    'lxml==3.4.1',              # 4.0.0
    'openpyxl==2.1.0',          # 2.5.0a3
    'xlrd==0.9.3',              # 1.1.0
    'XlsxWriter==0.9.3',        # 1.0.0
    'jsonpointer==1.10',        # 1.12
    'arrow==0.10.0',
    'transitions==0.2.4',       # 0.6.1
    'validate_email==1.3',
    'pandas==0.18.1',           # 0.20.3
    'html2text==2016.9.19',     # 2017.10.4
    'envoy==0.0.3',

]

test_requires = [
    # ----------------------------------------------
    #   testing
    # ----------------------------------------------
    'nose==1.3.3',              # 1.3.7
    'nose-exclude==0.2.0',      # 0.5.0
    'nose2-cov==1.0a4',
]

setup(name='patzilla',
      version='0.143.1',
      description='PatZilla is a modular patent information research platform and toolkit ' \
                  'with a modern user interface and access to multiple data sources.',
      long_description=README,
      license="AGPL 3, EUPL 1.2",
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Paste",
        "Framework :: Pyramid",
        "Intended Audience :: Developers",
        "Intended Audience :: Education",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: Information Technology",
        "Intended Audience :: Legal Industry",
        "Intended Audience :: Manufacturing",
        "Intended Audience :: Science/Research",
        # EUPL 1.2 isn't approved by OSI yet
        "License :: OSI Approved :: European Union Public Licence 1.1 (EUPL 1.1)",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: JavaScript",
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Scientific/Engineering",
      ],
      author='Andreas Motl',
      author_email='andreas.motl@ip-tools.org',
      url='https://github.com/ip-tools/ip-navigator',
      keywords='patent information research management trademark design search fulltext '
               'patent patents patent-search patent-data information information-retrieval intellectual-property '
               'research researcher researchers research-data research-tool research-and-development '
               'epo-ops dpma uspto open-data opendata '
      ,
      packages=find_packages(),
      include_package_data=True,
      package_data={
          'patzilla.navigator': [
              'resources/*.*',
              'templates/*.mako', 'templates/*.html', 'templates/*.min.js',
              'static/js/**/*.min.js', 'static/js/**/*.min.js.map', '**/**/*.css',
              '**/**/*.png', '**/**/*.jpg', '**/**/*.gif', '**/**/*.svg',
          ],
          'patzilla.util': ['*.js'],
      },
      zip_safe=False,
      test_suite='nose.collector',
      install_requires=requires,
      tests_require=test_requires,
      extras_require={
          'test': test_requires,
      },

      entry_points={
        'paste.app_factory': [
            'main = patzilla:main',
        ],

        # This is now a Beaker builtin as per "ext:mongodb"
        #'beaker.backends': [
        #    'mongodb = patzilla.util.database.beaker_mongodb:MongoDBNamespaceManager',
        #    ],

        'console_scripts': [
            'patzilla  = patzilla.commands:run',
        ],

      },

    )
