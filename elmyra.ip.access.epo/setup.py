import os

from setuptools import setup, find_packages
#from distutils.core import setup

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()
CHANGES = open(os.path.join(here, 'CHANGES.rst')).read()

requires = [

    # ----------------------------------------------
    #   backend
    # ----------------------------------------------
    # pyramid core
    #'pyramid==1.5a2',
    'pyramid==1.4.2',
    'pyramid_debugtoolbar',
    'pyramid_mako',
    'Akhet==2.0',
    'waitress',

    # web services
    'cornice==0.15',

    # ----------------------------------------------
    #   business logic
    # ----------------------------------------------
    'requests==2.0.0',

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

    # jquerui
    #'js.jqueryui==1.10.3',
    #'js.jqueryui_bootstrap==0.0.0',

    # fontawesome
    'css.fontawesome==3.2.1',

    # marionette, backbone and prerequisites
    'js.marionette==1.1.0a2',
    'js.underscore_string==2.3.0a1',
]

setup(name='elmyra.ip.access.epo',
      version='0.0.8',
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
      #packages=['elmyra.ip.access.epo'],
      include_package_data=True,
      package_data={'elmyra.ip.access.epo': ['**/*.mako', '**/**/*.js', '**/**/*.css', '**/**/*.jpg', '**/**/*.gif']},
      zip_safe=False,
      test_suite='elmyra.ip.access.epo',
      install_requires=requires,
      dependency_links=[
        'https://github.com/elmyra-org/js.marionette/tarball/1.1.0a2#egg=js.marionette-1.1.0a2',
      ],
      entry_points="""\
      [paste.app_factory]
      main = elmyra.ip.access.epo:main
      """,
      )
