# Copyright 2012 Rackspace Hosting, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import sys

from glob import glob
from distutils.core import Command
from unittest import TextTestRunner, TestLoader
from setuptools import setup
from subprocess import call
from os.path import splitext, basename, join as pjoin

from utils.dist import get_packages, get_data_files

TEST_PATHS = ['service_registry/test']

try:
    import epydoc
    has_epydoc = True
except ImportError:
    has_epydoc = False


# Commands based on Libcloud setup.py:
# https://github.com/apache/libcloud/blob/trunk/setup.py

class Pep8Command(Command):
    description = "Run pep8 script"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        try:
            import pep8
            pep8
        except ImportError:
            print ('Missing "pep8" library. You can install it using pip: '
                   'pip install pep8')
            sys.exit(1)

        cwd = os.getcwd()
        retcode = call(('pep8 %s/service_registry/' % (cwd)).split(' '))
        sys.exit(retcode)


class ApiDocsCommand(Command):
    description = "generate API documentation"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        if not has_epydoc:
            raise RuntimeError('Missing "epydoc" package!')

        os.system(
            'pydoctor'
            ' --add-package=service_registry'
            ' --project-name=service_registry'
        )


class TestCommand(Command):
    description = "Run tests"
    user_options = []

    def initialize_options(self):
        file_dir = os.path.abspath(os.path.split(__file__)[0])
        sys.path.insert(0, file_dir)
        for test_path in TEST_PATHS:
            sys.path.insert(0, pjoin(file_dir, test_path))
        self._dir = os.getcwd()

    def finalize_options(self):
        pass

    def _run_mock_api_server(self):
        from service_registry.test.utils import MockAPIServerRunner
        server = MockAPIServerRunner()
        server.setUp()

    def run(self):
        self._run_mock_api_server()

        testfiles = []
        for test_path in TEST_PATHS:
            for t in glob(pjoin(self._dir, test_path, 'test_*.py')):
                testfiles.append('.'.join(
                    [test_path.replace('/', '.'), splitext(basename(t))[0]]))

        tests = TestLoader().loadTestsFromNames(testfiles)

        t = TextTestRunner(verbosity=2)
        res = t.run(tests)
        return not res.wasSuccessful()


setup(
    name='service-registry',
    version='0.1.3',
    description='Python client for Rackspace Service Registry.',
    author='Rackspace Hosting, Inc.',
    author_email='sr@rackspace.com',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Framework :: Twisted'
    ],
    cmdclass={
        'pep8': Pep8Command,
        'apidocs': ApiDocsCommand,
        'test': TestCommand
    },
    packages=get_packages('service_registry'),
    package_dir={
        'service_registry': 'service_registry',
    },
    package_data={'service_registry': get_data_files('service_registry',
                                               parent='service_registry')},
    license='Apache License (2.0)',
    url='https://github.com/racker/python-service-registry-client',
    install_requires=[
        'python-dateutil >= 2.1',
        'requests >= 0.14.1',
        'apache-libcloud >= 0.11.3'
    ]
)
