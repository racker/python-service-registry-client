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

import mock
import unittest

from service_registry.client import Client, HeartBeater


class FarscapeClientTests(unittest.TestCase):
    def setUp(self):
        self.client = Client('user',
                             'api_key',
                             'http://127.0.0.1:8881/')

    def authenticate(fn):
        def wrapped(*args, **kwargs):
            name = 'service_registry.client.BaseClient._authenticate'
            with mock.patch(name) as _authenticate:
                _authenticate.return_value = {'X-Auth-Token': 'auth_token',
                                              'X-Tenant-Id': 'tenant_id'}
                fn(*args, **kwargs)
        return wrapped

    @authenticate
    def test_get_limits(self):
        expected = \
            {'rate':
                {'/.*': {'window': '24.0 hours', 'used': 0, 'limit': 500000}},
             'resource': {}}

        result = self.client.account.get_limits()
        self.assertEqual(result, expected)

    @authenticate
    def test_create_session(self):
        expected_keys = ['token']
        result = self.client.sessions.create(15)

        self.assertEqual(result[0].keys(), expected_keys)
        self.assertEqual(result[1], 'sessionId')
        self.assertTrue(isinstance(result[2], HeartBeater))
        self.assertEqual(result[2].heartbeat_interval, 12.0)
        self.assertEqual(result[2].heartbeat_timeout, 15)
        self.assertEqual(result[2].next_token, '6bc8d050-f86a-11e1-a89e-ca2ffe480b20')

    @authenticate
    def test_heartbeat_session(self):
        result = self.client.sessions.heartbeat('sessionId', 'someToken')

        self.assertTrue('token' in result)

    @authenticate
    def test_create_service(self):
        result = self.client.services.create('sessionId', 'dfw1-messenger')

        self.assertEqual(result, 'dfw1-messenger')

    @authenticate
    def test_get_service(self):
        expected_metadata = \
            {'region': 'dfw',
             'port': '5757',
             'ip': '127.0.0.1'}

        result = self.client.services.get('dfw1-messenger')

        self.assertEqual(result['id'], 'dfw1-messenger')
        self.assertEqual(result['session_id'], 'sessionId')
        self.assertEqual(result['tags'], ['tag1', 'tag2', 'tag3'])
        self.assertEqual(result['metadata'], expected_metadata)

    @authenticate
    def test_list_services(self):
        expected_metadata = \
            {'region': 'dfw',
             'port': '5757',
             'ip': '127.0.0.1'}

        result = self.client.services.list()

        self.assertEqual(result['values'][0]['id'], 'dfw1-api')
        self.assertEqual(result['values'][0]['session_id'], 'sessionId')
        self.assertTrue('tags' in result['values'][0])
        self.assertTrue('metadata' in result['values'][0])
        self.assertEqual(result['values'][1]['id'], 'dfw1-messenger')
        self.assertEqual(result['values'][1]['session_id'], 'sessionId')
        self.assertEqual(result['values'][1]['tags'],
                         ['tag1', 'tag2', 'tag3'])
        self.assertEqual(result['values'][1]['metadata'],
                         expected_metadata)
        self.assertTrue('metadata' in result)

    @authenticate
    def test_list_for_tag(self):
        expected_metadata = \
            {'region': 'dfw',
             'port': '5757',
             'ip': '127.0.0.1'}

        result = self.client.services.list_for_tag('tag1')

        self.assertEqual(result['values'][0]['id'], 'dfw1-messenger')
        self.assertEqual(result['values'][0]['session_id'], 'sessionId')
        self.assertEqual(result['values'][0]['tags'],
                         ['tag1', 'tag2', 'tag3'])
        self.assertEqual(result['values'][0]['metadata'],
                         expected_metadata)
        self.assertTrue('metadata' in result)

    @authenticate
    def test_get_sessions(self):
        result = self.client.sessions.list()

        self.assertEqual(result['values'][0]['id'], 'sessionId')
        self.assertEqual(result['values'][0]['heartbeat_timeout'], 30)
        self.assertTrue('metadata' in result['values'][0])
        self.assertTrue('last_seen' in result['values'][0])
        self.assertTrue('metadata' in result)

    @authenticate
    def test_get_session(self):
        result = self.client.sessions.get('sessionId')

        self.assertEqual(result['id'], 'sessionId')
        self.assertEqual(result['heartbeat_timeout'], 30)
        self.assertTrue('metadata' in result)
        self.assertTrue('last_seen' in result)

    @authenticate
    def test_list_configuration(self):
        result = self.client.configuration.list()

        self.assertEqual(result['values'][0]['id'], 'configId')
        self.assertEqual(result['values'][0]['value'], 'test value 123456')
        self.assertTrue('metadata' in result)

    @authenticate
    def test_get_configuration(self):
        result = self.client.configuration.get('configId')

        self.assertEqual(result['id'], 'configId')
        self.assertEqual(result['value'], 'test value 123456')

if __name__ == '__main__':
    unittest.main()
