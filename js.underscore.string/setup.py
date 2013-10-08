from setuptools import setup, find_packages
import os

version = '2.3.0'


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('README.rst')
    + '\n' +
    read('js', 'underscore', 'string', 'test_underscore_string.txt')
    + '\n' +
    read('CHANGES.rst'))

setup(
    name='js.underscore.string',
    version=version,
    description="fanstatic underscore.string",
    long_description=long_description,
    classifiers=[],
    keywords='',
    author='Andreas Motl',
    author_email='andreas.motl@elmyra.de',
    url='https://github.com/amotl/js.underscore.string',
    license='BSD',
    packages=find_packages(),
    namespace_packages=['js'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'fanstatic',
        'setuptools',
        'js.underscore==1.4.4',
    ],
    entry_points={
        'fanstatic.libraries': [
            'underscore_string = js.underscore.string:library',
        ],
    },
)
