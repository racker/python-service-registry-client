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

from distutils.core import Command
from setuptools import setup
from subprocess import call

from utils.dist import get_packages, get_data_files

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
        retcode = call(('pep8 %s/farscape_client/' % (cwd)).split(' '))
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
            ' --add-package=farscape_client'
            ' --project-name=farscape_client'
        )


class TestCommand(Command):
    description = "Run tests"
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def _run_mock_api_server(self):
        server = MockAPIServerRunner()
        server.setUp()

    def run(self):
        self._run_mock_api_server()
        cwd = os.getcwd()
        # TODO
        #retcode = call(('trial %s/farscape_client/test/' % (cwd)).split(' '))
        #sys.exit(retcode)


setup(
    name='farscape_client',
    version='0.1.0',
    description='Twisted Farscape API Client',
    author='Rackspace Hosting, Inc.',
    author_email='shawn.smith@rackspace.com',
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
    packages=get_packages('farscape_client'),
    package_dir={
        'farscape_client': 'farscape_client',
    },
    package_data={'farscape_client': get_data_files('farscape_client',
                                               parent='farscape_client')},
    license='Apache License (2.0)',
    url='https://github.com/racker/python-twisted-farscape-client',
    install_requires=['Twisted'],
)
