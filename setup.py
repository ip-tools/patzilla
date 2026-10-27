import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

requires = [

    # ----------------------------------------------
    #   Environment
    # ----------------------------------------------
    'setuptools<81',
    'six>=1.10.0',
    'mock',

    # ----------------------------------------------
    #   Backend
    # ----------------------------------------------

    # Pyramid core
    'pyramid<2',
    'hupper<2',
    'watchdog<7',
    'pyramid-debugtoolbar<5',
    'Pygments<3',
    'pyramid-mako<2',
    'Mako<2',
    'Jinja2>=2.11.3,<4',
    'MarkupSafe<4',
    'Akhet<3',
    'waitress>=1,<4',
    'Paste<3',                  # 3.10.1
    'PasteDeploy<4',
    'PasteScript<3',            # 3.7.0

    # Caching
    'Beaker<2',
    'pyramid_beaker<0.10',
    'dogpile.cache<2',
    'platformdirs<5',
    'repoze-lru<0.9',

    # Database and storage
    # Can't upgrade to pymongo-3.5.1 due to "from pymongo.connection import Connection"
    # usage in "mongodb_gridfs_beaker" module.
    'pymongo<5',
    'mongodb_gridfs_beaker @ git+https://github.com/loucash/mongodb_gridfs_beaker@master',
    'mongoengine==0.20.0',      # 0.29.3
    'python-magic<1',

    # Web services
    'cornice<3',                # 6.1.0

    # Authorization
    'pycryptodome>=3,<4',
    'python-jwt<5',
    'pbkdf2<1.4',


    # ----------------------------------------------
    #   Protocols and data formats
    # ----------------------------------------------

    # HTTP
    'python-epo-ops-client<5',
    'requests<3',
    'mechanize<1',
    'MechanicalSoup<2',

    # HTTP SNI support
    'pyOpenSSL',
    'cryptography<43',
    'pyasn1<1',
    'ndg-httpsclient<1',

    # HTML
    'beautifulsoup4<5',
    'html2text', 

    # XML
    'lxml>=4.6.5,<7',
    'xmljson<1',

    # JSON
    'jsonpointer<4',


    # ----------------------------------------------
    #   Data handling and formatting
    # ----------------------------------------------

    # Data handling
    'attrs<27',
    'munch<5',
    'pyparsing<4',
    'python-dateutil<3',
    'ago<0.2',
    'arrow<2',
    'validate_email<2',
    'numpy>=1.16.6,<3',
    'pandas<3',
    'pathlib2',

    # Data formatting
    'openpyxl<4',
    'xlrd3<2',
    'XlsxWriter<4',

    # Data conversion
    'Pillow>=6,<14',
    # 'unoconv<1',

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
    'docopt-ng<1',
    'click>=7,<8',
    'envoy<0.1',
    'where<2',
    'tqdm<5',

]

test_requires = [
    # -----------
    #   Testing
    # -----------
    'pytest>=4,<10',
    'pytest-cov>=2,<8',
    'pytest-xdist<4',
    'testfixtures>=6,<8',
    'pytest-forked>=1,<2',
    'types-lxml',
]

setup(name='patzilla',
      version='0.170.0',
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
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Programming Language :: Python :: 3.14",
        "Programming Language :: Python :: 3.15",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
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
