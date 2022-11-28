import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

requires = [

    # ----------------------------------------------
    #   Environment
    # ----------------------------------------------
    'six>=1.10.0',
    'mock>=3,<4',  # 4.0.3

    # ----------------------------------------------
    #   Backend
    # ----------------------------------------------

    # Pyramid core
    'pyramid==1.9.1',           # 1.9.4, 1.10.8, 2.0
    'hupper==1.10.2',           # 1.10.3
    'watchdog==0.10.7',         # 2.1.7
    'pyramid-debugtoolbar==4.3',  # 4.9
    'Pygments==2.5.2',          # 2.11.2
    'pyramid-mako==1.0.2',      # 1.1.0
    'Mako==1.0.0',              # 1.2.0
    'Jinja2>=2.11.3,<3',        # 3.1.1
    'MarkupSafe==1.1.1',        # 2.1.1
    'Akhet==2.0',
    'waitress>=1,<2',           # 2.1.1
    'Paste==2.0.3',             # 3.5.0
    'PasteScript==2.0.2',       # 3.2.1

    # Caching
    'Beaker==1.9.0',            # 1.11.0
    'pyramid_beaker==0.8',
    'dogpile.cache==0.6.4',     # 0.6.8, 0.7.1, 0.8.0, 0.9.2, 1.1.5
    'appdirs>=1,<2',

    # Database and storage
    # Can't upgrade to pymongo-3.5.1 due to "from pymongo.connection import Connection"
    # usage in "mongodb_gridfs_beaker" module.
    'pymongo==2.9.5',           # 3.12.3, 4.1.1
    'mongodb_gridfs_beaker==0.5.4',
    'mongoengine==0.13.0',      # 0.24.1
    'minio==4.0.14',            # 7.1.6
    'python-magic==0.4.15',     # 0.4.25

    # Web services
    'cornice==2.4.1',           # 3.4.0, 3.6.1, 4.0.1, 5.2.0, 6.0.1

    # Authorization
    'pycryptodome>=3,<4',
    'python-jwt>=3.3.2,<4',
    'pbkdf2==1.3',


    # ----------------------------------------------
    #   Protocols and data formats
    # ----------------------------------------------

    # HTTP
    'python-epo-ops-client==3.1.3',     # 4.0.0
    'requests<=2.27.1',
    'requests-cache<0.6',
    'mechanize==0.3.6',         # 0.4.8
    'MechanicalSoup==1.0.0',    # 1.1.0
    'beautifulsoup4==4.9.3',    # 4.11.1

    # HTTP SNI support
    'pyOpenSSL==19.0.0',        # 22.0.0
    'cryptography>=3.2,<3.4',   # 36.0.2
    'pyasn1==0.4.5',            # 0.4.8
    'ndg-httpsclient==0.5.1',

    # HTML
    'BeautifulSoup==3.2.1',     # 3.2.2
    'html2text==2016.9.19',     # 2020.1.16

    # XML
    # Remark: Both lxml 3.8.0 and 4.0.0 will segfault on Debian Wheezy (7.11)
    #'lxml==3.4.1',             # 4.2.0
    'lxml>=4.6.5,<5',
    'xmljson==0.1.9',           # 0.2.1

    # JSON
    'jsonpointer==1.14',        # 2.3


    # ----------------------------------------------
    #   Data handling and formatting
    # ----------------------------------------------

    # Data handling
    'attrs',
    'Bunch==1.0.1',             # Maybe switch to "Munch"
    'pyparsing==2.0.2',         # 2.2.2, 2.3.1, 2.4.7, 3.0.8
    'python-dateutil==2.6.1',   # 2.7.7, 2.8.2
    'ago==0.0.9',               # 0.0.93
    'arrow==0.10.0',            # 0.12.1
    'validate_email==1.3',
    'numpy==1.16.6',            # 1.22.3
    'pandas==0.18.1',           # 0.22.0, 0.25.3, 1.4.2

    # Data formatting
    'openpyxl==2.1.0',          # 2.1.5, 2.6.4, 3.0.9
    'xlrd==0.9.3',              # 0.9.4, 1.2.0, 2.0.1
    'XlsxWriter==0.9.3',        # 1.4.5, 2.0.0, 3.0.3

    # Data conversion
    'Pillow>=6,<7',             # 9.1.0

    # Does not work from within virtualenv?
    # 'unoconv==0.8.2',          # 0.9.0


    # ----------------------------------------------
    #   Program flow
    # ----------------------------------------------
    'blinker==1.4',
    'transitions==0.2.4',       # 0.2.9, ..., 0.8.11


    # ----------------------------------------------
    #   Console and system interfaces
    # ----------------------------------------------
    'docopt==0.6.2',
    'click>=7,<8',
    'envoy==0.0.3',
    'where==1.0.2',
    'tqdm==4.23.4',             # 4.64.0

]

test_requires = [
    # -----------
    #   Testing
    # -----------
    'pytest>=4,<5',             # 5.4.3, 6.2.5, 7.1.1
    'pytest-cov>=2,<3',         # 3.0.0
    'coverage>=5.3.1,<6',       # 6.3.2
    'testfixtures>=6,<7',
    'pytest-forked>=1,<2',
]

setup(name='patzilla',
      version='0.169.3',
      description='PatZilla is a modular patent information research platform and data integration ' \
                  'toolkit. It features a modern user interface and access to multiple data sources.',
      long_description=README,
      license="AGPL 3, EUPL 1.2",
      classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
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
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Natural Language :: English",
        "Operating System :: MacOS",
        "Operating System :: POSIX",
        "Programming Language :: JavaScript",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Topic :: Communications",
        "Topic :: Database",
        "Topic :: Internet",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Human Machine Interfaces",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Scientific/Engineering :: Interface Engine/Protocol Translator",
        "Topic :: Scientific/Engineering :: Visualization",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Archiving",
        "Topic :: Text Processing",
        "Topic :: Utilities",
      ],
      author='Andreas Motl',
      author_email='andreas.motl@ip-tools.org',
      url='https://github.com/ip-tools/patzilla',
      keywords='epo ops espacenet dpma depatisnet dpmaregister depatisconnect uspto appft patft '
               'cipo ificlaims mtc depatech '
               'open-data opendata research analysis technology research-data research-tool '
               'intellectual-property patent trademark design information information-retrieval '
               'fulltext search search-engine query-language patent-search patent-data '
               'research-and-development management'
      ,
      packages=find_packages(),
      include_package_data=True,
      package_data={
          'patzilla.navigator': [
              'resources/*.*',
              'templates/*.mako', 'templates/*.html', 'templates/*.min.js',
              'static/js/**/*.min.js', 'static/js/**/*.min.js.map', '**/**/*.css',
              '**/**/*.png', '**/**/*.jpg', '**/**/*.gif', '**/**/*.svg', '**/**/*.txt',
          ],
          'patzilla.util': ['*.js'],
      },
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={
          'test': test_requires,
      },
      dependency_links=[
      ],

      entry_points={
        'paste.app_factory': [
            'web     = patzilla:web',
            'minimal = patzilla:minimal',
        ],

        # This is now a Beaker builtin as per "ext:mongodb"
        #'beaker.backends': [
        #    'mongodb = patzilla.util.database.beaker_mongodb:MongoDBNamespaceManager',
        #    ],

        'console_scripts': [
            'patzilla      = patzilla.commands:cli',
            'patzilla-user = patzilla.commands:usercmd',
            'dpmaregister  = patzilla.access.dpma.dpmaregister:run',
            'patzilla-sip  = patzilla.access.sip.commands:run',
            'patzilla-cachecarver = patzilla.util.database.beaker_mongodb_carve:run',
        ],

      },

    )
