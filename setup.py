# -*- coding: utf-8 -*-
import re
from setuptools import setup, find_packages

REQUIRES = [
    'aiohttp>=3',
    'python-mimeparse',
    'gunicorn',
]


def find_version(fname):
    """Attempts to find the version number in the file names fname.
    Raises RuntimeError if not found.
    """
    version = ''
    with open(fname, 'r') as fp:
        reg = re.compile(r'__version__ = [\'"]([^\'"]*)[\'"]')
        for line in fp:
            m = reg.match(line)
            if m:
                version = m.group(1)
                break
    if not version:
        raise RuntimeError('Cannot find version information')
    return version

__version__ = find_version('aiohttp_utils/__init__.py')


def read(fname):
    with open(fname) as fp:
        content = fp.read()
    return content

setup(
    name='aiohttp-utils',
    version=__version__,
    description='Handy utilities for aiohttp.web applications.',
    long_description=read('README.rst'),
    long_description_content_type='text/x-rst',
    author='Steven Loria',
    author_email='sloria1@gmail.com',
    url='https://github.com/sloria/aiohttp-utils',
    packages=find_packages(exclude=("test*", )),
    package_dir={'aiohttp-utils': 'aiohttp_utils'},
    include_package_data=True,
    install_requires=REQUIRES,
    license='MIT',
    zip_safe=False,
    keywords='aiohttp_utils aiohttp utilities aiohttp.web',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ],
    test_suite='tests'
)
