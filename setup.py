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
    'pyramid<1.10',             # 1.10.8, 2.0
    'hupper<2',
    'watchdog<1',               # 2.1.9
    'pyramid-debugtoolbar==4.3',  # 4.9
    'Pygments==2.5.2',          # 2.13.0
    'pyramid-mako<2',
    'Mako<2',
    'Jinja2>=2.11.3,<3',        # 3.1.2
    'MarkupSafe<2',             # 2.1.1
    'Akhet==2.0',
    'waitress>=1,<2',           # 2.1.2
    'Paste<3',                  # 3.5.2
    'PasteDeploy<3',            # 3.0.1
    'PasteScript<3',            # 3.2.1

    # Caching
    'Beaker<2',
    'pyramid_beaker==0.8',
    'dogpile.cache<1',          # 1.1.8
    'platformdirs<3',

    # Database and storage
    # Can't upgrade to pymongo-3.5.1 due to "from pymongo.connection import Connection"
    # usage in "mongodb_gridfs_beaker" module.
    'pymongo',                # 3.13.0, 4.3.3
    'mongodb_gridfs_beaker==0.6.0dev1',
    'mongoengine',      # 0.24.1
    'python-magic<1',

    # Web services
    'cornice<3',                # 3.4.4, 3.6.1, 4.0.1, 5.2.0, 6.0.1

    # Authorization
    'pycryptodome>=3,<4',
    'python-jwt>=3.3.4,<4',
    'pbkdf2==1.3',


    # ----------------------------------------------
    #   Protocols and data formats
    # ----------------------------------------------

    # HTTP
    'python-epo-ops-client<4',  # 4.0.0
    'requests<3',
    'mechanize<1',
    'MechanicalSoup<2',
    'beautifulsoup4<5',

    # HTTP SNI support
    'pyOpenSSL==19.0.0',        # 22.0.0
    'cryptography>=3.2,<3.4',   # 36.0.2
    'pyasn1<1',
    'ndg-httpsclient<1',

    # HTML
    'beautifulsoup4',
    'html2text', 

    # XML
    # Remark: Both lxml 3.8.0 and 4.0.0 will segfault on Debian Wheezy (7.11)
    #'lxml==3.4.1',             # 4.2.0
    'lxml>=4.6.5,<5',
    'xmljson<1',

    # JSON
    'jsonpointer<3',


    # ----------------------------------------------
    #   Data handling and formatting
    # ----------------------------------------------

    # Data handling
    'attrs',
    'Bunch',             # Maybe switch to "Munch"
    'pyparsing',
    'python-dateutil<3',
    'ago==0.0.9',               # 0.0.93
    'arrow==0.10.0',            # 0.12.1
    'validate_email<2',
    'numpy==1.16.6',            # 1.22.3
    'pandas',           # 0.22.0, 0.25.3, 1.4.2
    'pathlib',

    # Data formatting
    'openpyxl>=2.4.2,<3',
    'xlrd3',
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
    'docopt<1',
    'click>=7,<8',
    'envoy==0.0.3',
    'where==1.0.2',
    'tqdm<5',

]

test_requires = [
    # -----------
    #   Testing
    # -----------
    'pytest>=4,<5',             # 5.4.3, 6.2.5, 7.1.1
    'pytest-cov>=2,<3',         # 3.0.0
    'pytest-xdist<2',           # 3.0.2
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
          'https://github.com/ip-tools/mongodb_gridfs_beaker/archive/0.6.0dev1.tar.gz#egg=mongodb_gridfs_beaker',
          'https://github.com/ip-tools/mechanize/archive/v0.4.3dev2.tar.gz#egg=mechanize-0.4.3dev2',
          #'https://github.com/dagwieers/unoconv/archive/master.tar.gz#egg=unoconv-0.8.2',
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
