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

from service_registry.client import Client
from service_registry.heartbeater import HeartBeater

TOKENS = ['6bc8d050-f86a-11e1-a89e-ca2ffe480b20']

EXPECTED_METADATA = \
    {'region': 'dfw',
     'port': '3306',
     'ip': '127.0.0.1',
     'version': '5.5.24-0ubuntu0.12.04.1 (Ubuntu)'}


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
    def test_create_services(self):
        response_body = {'token': TOKENS[0]}
        result = self.client.services.create('dfw1-db1', 30)

        self.assertEqual(result[0], response_body)
        self.assertTrue(isinstance(result[1], HeartBeater))
        self.assertEqual(result[1].heartbeat_interval, 24.0)
        self.assertEqual(result[1].heartbeat_timeout, 30)
        self.assertEqual(result[1].next_token, TOKENS[0])

    @authenticate
    def test_heartbeat_service(self):
        result = self.client.services.heartbeat('dfw1-db1', 'someToken')

        self.assertEqual(result, {'token': TOKENS[0]})

    @authenticate
    def test_get_service(self):
        result = self.client.services.get('dfw1-db1')
        self.assertEqual(result['id'], 'dfw1-db1')
        self.assertEqual(result['heartbeat_timeout'], 30)
        self.assertEqual(result['tags'], ['db', 'mysql'])
        self.assertEqual(result['metadata'], EXPECTED_METADATA)

    @authenticate
    def test_list_services(self):
        result = self.client.services.list()

        self.assertEqual(result['values'][0]['id'], 'dfw1-api')
        self.assertEqual(result['values'][0]['heartbeat_timeout'], 30)
        self.assertTrue('tags' in result['values'][0])
        self.assertTrue('metadata' in result['values'][0])
        self.assertEqual(result['values'][1]['id'], 'dfw1-db1')
        self.assertEqual(result['values'][1]['tags'],
                         ['db', 'mysql'])
        self.assertEqual(result['values'][1]['metadata'],
                         EXPECTED_METADATA)
        self.assertTrue('metadata' in result)

    @authenticate
    def test_list_for_tag(self):
        result = self.client.services.list_for_tag('db')

        self.assertEqual(result['values'][0]['id'], 'dfw1-db1')
        self.assertEqual(result['values'][0]['heartbeat_timeout'], 30)
        self.assertEqual(result['values'][0]['tags'],
                         ['db', 'mysql'])
        self.assertEqual(result['values'][0]['metadata'],
                         EXPECTED_METADATA)
        self.assertTrue('metadata' in result)

    @authenticate
    def test_list_configuration(self):
        result = self.client.configuration.list()

        self.assertEqual(result['values'][0]['id'], 'configId')
        self.assertEqual(result['values'][0]['value'], 'test value 123456')
        self.assertTrue('metadata' in result)

    @authenticate
    def test_list_configuration_for_namespace(self):
        namespaces = ['/api/', '/api', 'api']

        for namespace in namespaces:
            kwargs = {'namespace': namespace}
            result = self.client.configuration.list_for_namespace(**kwargs)

            self.assertEqual(result['values'][0]['id'], '/api/key-1')
            self.assertEqual(result['values'][0]['value'], 'test value 123456')
            self.assertEqual(result['values'][1]['id'], '/api/key-2')
            self.assertEqual(result['values'][1]['value'], 'test value 23456')
            self.assertTrue('metadata' in result)

    @authenticate
    def test_get_configuration(self):
        result = self.client.configuration.get('configId')

        self.assertEqual(result['id'], 'configId')
        self.assertEqual(result['value'], 'test value 123456')

    @mock.patch('service_registry.client.BaseClient.request')
    def _marker_assertion(self, path, request):
        client = getattr(self.client, path.strip('/'))
        client.list(marker='someMarker')
        request.assert_called_with('GET', path,
                                   options={'marker': 'someMarker'})

    @mock.patch('service_registry.client.BaseClient.request')
    def _limit_assertion(self, path, request):
        client = getattr(self.client, path.strip('/'))
        client.list(limit=3)
        request.assert_called_with('GET', path, options={'limit': 3})

    @mock.patch('service_registry.client.BaseClient.request')
    def _marker_and_limit_assertion(self, path, request):
        client = getattr(self.client, path.strip('/'))
        client.list(marker='someMarker', limit=3)
        request.assert_called_with('GET', path,
                                   options={'marker': 'someMarker',
                                            'limit': 3})

    def test_list_services_with_marker_calls_request_with_marker(self):
        return self._marker_assertion('/services')

    def test_list_events_with_marker_calls_request_with_marker(self):
        return self._marker_assertion('/events')

    def test_list_configuration_with_marker_calls_request_with_marker(self):
        return self._marker_assertion('/configuration')

    def test_list_services_with_limit_calls_request_with_limit(self):
        return self._limit_assertion('/services')

    def test_list_events_with_limit_calls_request_with_limit(self):
        return self._limit_assertion('/events')

    def test_list_configuration_with_limit_calls_request_with_limit(self):
        return self._limit_assertion('/configuration')

    def test_list_services_with_marker_and_limit(self):
        return self._marker_and_limit_assertion('/services')

    def test_list_events_with_mark_and_limit(self):
        return self._marker_and_limit_assertion('/events')

    def test_list_configuration_with_marker_and_limit(self):
        return self._marker_and_limit_assertion('/configuration')

    @mock.patch("service_registry.client.BaseClient.request")
    def test_list_for_tag_with_marker(self, request):
        self.client.services.list_for_tag('someTag', marker='someMarker')
        request.assert_called_with('GET', '/services',
                                   options={'tag': 'someTag',
                                            'marker': 'someMarker'})

    @mock.patch('service_registry.client.BaseClient.request')
    def test_list_for_tag_with_limit(self, request):
        self.client.services.list_for_tag('someTag', limit=3)
        request.assert_called_with('GET', '/services',
                                   options={'tag': 'someTag',
                                            'limit': 3})

    @mock.patch('service_registry.client.BaseClient.request')
    def test_list_for_tag_with_marker_and_limit(self, request):
        self.client.services.list_for_tag('someTag', marker='someMarker',
                                          limit=3)
        request.assert_called_with('GET', '/services',
                                   options={'tag': 'someTag',
                                            'marker': 'someMarker',
                                            'limit': 3})

if __name__ == '__main__':
    unittest.main()
