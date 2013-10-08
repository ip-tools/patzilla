from setuptools import setup, find_packages
import os

version = '1.0.0'


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('README.rst')
    + '\n' +
    read('js', 'jquery_shorten', 'test_jquery_shorten.txt')
    + '\n' +
    read('CHANGES.rst'))

setup(
    name='js.jquery_shorten',
    version=version,
    description="fanstatic jquery.shorten",
    long_description=long_description,
    classifiers=[],
    keywords='',
    author='Andreas Motl',
    author_email='andreas.motl@elmyra.de',
    url='https://github.com/amotl/js.jquery_shorten',
    license='BSD',
    packages=find_packages(),
    namespace_packages=['js'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'fanstatic',
        'setuptools',
        'js.jquery==1.9.1',
    ],
    entry_points={
        'fanstatic.libraries': [
            'jquery_shorten = js.jquery_shorten:library',
        ],
    },
)
