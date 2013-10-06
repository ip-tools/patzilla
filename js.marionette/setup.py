from setuptools import setup, find_packages
import os

version = '1.1.0'


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('README.rst')
    + '\n' +
    read('js', 'marionette', 'test_marionette.txt')
    + '\n' +
    read('CHANGES.rst'))

setup(
    name='js.marionette',
    version=version,
    description="fanstatic backbone.marionette",
    long_description=long_description,
    classifiers=[],
    keywords='',
    author='Andreas Motl',
    author_email='andreas.motl@elmyra.de',
    url='https://github.com/amotl/js.marionette',
    license='BSD',
    packages=find_packages(),
    namespace_packages=['js'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'fanstatic',
        'setuptools',
        'js.backbone==1.0.0',
        'js.underscore==1.4.4',
        'js.json2==2011-02-23',
    ],
    entry_points={
        'fanstatic.libraries': [
            'marionette = js.marionette:library',
        ],
    },
)
