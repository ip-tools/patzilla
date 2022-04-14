import os
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
#CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [

    # ----------------------------------------------
    #   Environment
    # ----------------------------------------------
    #'setuptools==36.4.0',       # 38.5.2
    'six>=1.10.0',              # 1.11.0


    # ----------------------------------------------
    #   Backend
    # ----------------------------------------------

    # Pyramid core
    'pyramid==1.9.1',
    'hupper==1.10.2',
    'watchdog==0.10.7',
    'pyramid-debugtoolbar==4.3',    # 4.4
    'Pygments==2.5.2',
    'pyramid-mako==1.0.2',
    'Mako==1.0.0',
    'Jinja2>=2.11.3,<3',
    'MarkupSafe==1.1.1',
    'Akhet==2.0',
    'waitress>=1,<2',
    'Paste==2.0.3',
    'PasteScript==2.0.2',

    # Caching
    'Beaker==1.9.0',            # 1.10.0
    'pyramid_beaker==0.8',
    'dogpile.cache==0.6.4',     # 0.6.5

    # Database and storage
    # Can't upgrade to pymongo-3.5.1 due to "from pymongo.connection import Connection"
    # usage in "mongodb_gridfs_beaker" module.
    'pymongo==2.9.5',           # 3.6.1
    'mongodb_gridfs_beaker==0.5.4',
    'mongoengine==0.13.0',      # 0.15.0
    'minio==4.0.14',
    'python-magic==0.4.15',

    # Web services
    'cornice==2.4.1',           # 3.4.0

    # Authorization
    'pycryptodome>=3,<4',
    'jws==0.1.3',
    'python-jwt==2.0.2',        # 3.1.0
    'pbkdf2==1.3',


    # ----------------------------------------------
    #   Protocols and data formats
    # ----------------------------------------------

    # HTTP
    'python-epo-ops-client==3.1.1',
    'requests<=2.27.1',
    'mechanize==0.3.6',
    'MechanicalSoup==0.10.0',
    'beautifulsoup4==4.9.3',

    # HTTP SNI support
    'pyOpenSSL==19.0.0',
    'cryptography>=3.2,<3.4',
    'pyasn1==0.4.5',
    'ndg-httpsclient==0.5.1',

    # HTML
    'BeautifulSoup==3.2.1',     # beautifulsoup4==4.6.0
    'html2text==2016.9.19',     # 2018.1.9

    # XML
    # Remark: Both lxml 3.8.0 and 4.0.0 will segfault on Debian Wheezy (7.11)
    #'lxml==3.4.1',              # 4.2.0
    'lxml>=4.6.5,<5',
    'xmljson==0.1.9',

    # JSON
    'jsonpointer==1.14',        # 2.0


    # ----------------------------------------------
    #   Data handling and formatting
    # ----------------------------------------------

    # Data handling
    'attrs',
    'Bunch==1.0.1',             # Maybe switch to "Munch"
    'pyparsing==2.0.2',         # 2.2.0
    'python-dateutil==2.6.1',   # 2.7.0
    'ago==0.0.9',               # 0.0.92
    'arrow==0.10.0',            # 0.12.1
    'validate_email==1.3',
    'numpy==1.16.6',
    'pandas==0.18.1',           # 0.22.0

    # Data formatting
    'openpyxl==2.1.0',          # 2.5.4
    'xlrd==0.9.3',              # 1.1.0
    'XlsxWriter==0.9.3',        # 1.0.5

    # Data conversion
    'Pillow>=6,<7',
    #'unoconv==0.8.2',          # Does not work from within virtualenv


    # ----------------------------------------------
    #   Program flow
    # ----------------------------------------------
    'blinker==1.4',
    'transitions==0.2.4',       # 0.6.4


    # ----------------------------------------------
    #   Console and system interfaces
    # ----------------------------------------------
    'docopt==0.6.2',
    'envoy==0.0.3',
    'where==1.0.2',
    'tqdm==4.23.4',

]

test_requires = [
    # -----------
    #   Testing
    # -----------
    'pytest>=4,<5',
    'pytest-cov>=2,<3',
    'coverage>=5.3.1,<6',
    'mock>=3,<4',
    'testfixtures>=6,<7',
]

setup(name='patzilla',
      version='0.169.3',
      description='PatZilla is a modular patent information research platform and data integration ' \
                  'toolkit. It features a modern user interface and access to multiple data sources.',
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
        "License :: OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: JavaScript",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        "Topic :: Scientific/Engineering",
      ],
      author='Andreas Motl',
      author_email='andreas.motl@ip-tools.org',
      url='https://github.com/ip-tools/patzilla',
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
          #'https://github.com/MechanicalSoup/MechanicalSoup/archive/master.tar.gz#egg=MechanicalSoup-1.0.0-dev',
          #'https://github.com/dagwieers/unoconv/archive/master.tar.gz#egg=unoconv-0.8.2',
      ],

      entry_points={
        'paste.app_factory': [
            'main = patzilla:main',
        ],

        # This is now a Beaker builtin as per "ext:mongodb"
        #'beaker.backends': [
        #    'mongodb = patzilla.util.database.beaker_mongodb:MongoDBNamespaceManager',
        #    ],

        'console_scripts': [
            'patzilla      = patzilla.commands:run',
            'patzilla-user = patzilla.commands:usercmd',
            'dpmaregister  = patzilla.access.dpma.dpmaregister:run',
            'patzilla-sip  = patzilla.access.sip.commands:run',
            'patzilla-cachecarver = patzilla.util.database.beaker_mongodb_carve:run',
        ],

      },

    )
