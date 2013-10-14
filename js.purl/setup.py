from setuptools import setup, find_packages
import os

version = '2.3.1a1'


def read(*rnames):
    return open(os.path.join(os.path.dirname(__file__), *rnames)).read()

long_description = (
    read('README.rst')
    + '\n' +
    read('js', 'purl', 'test_purl.txt')
    + '\n' +
    read('CHANGES.rst'))

setup(
    name='js.purl',
    version=version,
    description="fanstatic purl",
    long_description=long_description,
    classifiers=[],
    keywords='',
    author='Andreas Motl',
    author_email='andreas.motl@elmyra.de',
    url='https://github.com/elmyra/js.purl',
    license='MIT',
    packages=find_packages(),
    namespace_packages=['js'],
    include_package_data=True,
    package_data={'js.purl': ['**/*.js']},
    zip_safe=False,
    install_requires=[
        'fanstatic',
        'setuptools',
    ],
    entry_points={
        'fanstatic.libraries': [
            'purl = js.purl:library',
        ],
    },
)
