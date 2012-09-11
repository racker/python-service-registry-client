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

from copy import deepcopy

import libcloud.security
from libcloud.common.types import InvalidCredsError, MalformedResponseError
from libcloud.compute.drivers.rackspace import RackspaceNodeDriver
import requests

libcloud.security.VERIFY_SSL_CERT = False

US_AUTH_URL = 'https://identity.api.rackspacecloud.com/v2.0/tokens'
UK_AUTH_URL = 'https://lon.identity.api.rackspacecloud.com/v2.0/tokens'
DEFAULT_AUTH_URLS = {'us': US_AUTH_URL,
                     'uk': UK_AUTH_URL}
DEFAULT_API_URL = 'https://fs-staging.k1k.me/v1.0/'


class BaseClient(object):
    def __init__(self, base_url, auth_headers):
        self.base_url = base_url
        self.auth_headers = auth_headers

    def request(self, method, path, options=None,
                payload=None, heartbeater=None):
        request_url = self.base_url + path
        if method == 'GET':
            r = requests.get(request_url, headers=self.auth_headers, params=options)
            return r.json
#        elif method == 'POST':


class SessionsClient(BaseClient):
    def __init__(self, base_url, auth_headers):
        super(SessionsClient, self).__init__(base_url, auth_headers)
        self.sessions_path = '/sessions'

    def list(self):
        path = self.sessions_path

        return self.request('GET', path)

    def get(self, session_id):
        path = '%s/%s' % (self.sessions_path, session_id)

        return self.request('GET', path)

    def heartbeat(self, session_id, token):
        path = '%s/%s/heartbeat' % (self.sessions_path, session_id)
        payload = {'token': token}

        return self.request('POST', path, payload=payload)

    def update(self, session_id, payload):
        path = '%s/%s' % (self.sessions_path, session_id)

        return self.request('PUT', path, payload=payload)


class EventsClient(BaseClient):
    def __init__(self, base_url, auth_headers):
        super(EventsClient, self).__init__(base_url, auth_headers)
        self.events_path = '/events'

    def list(self, marker=None):
        options = None
        if marker:
            options = {'marker': marker}

        return self.request('GET', self.events_path, options=options)


class ServicesClient(BaseClient):
    def __init__(self, base_url, auth_headers):
        super(ServicesClient, self).__init__(base_url, auth_headers)
        self.services_path = '/services'

    def list(self):
        return self.request('GET', self.services_path)

    def listForTag(self, tag):
        options = {'tag': tag}

        return self.request('GET', self.services_path, options=options)

    def get(self, service_id):
        path = '%s/%s' % (self.services_path, service_id)

        return self.request('GET', path)

    def create(self, session_id, service_id, payload=None):
        payload = deepcopy(payload) if payload else {}
        payload['session_id'] = session_id
        payload['id'] = service_id

        return self.request('POST', self.services_path, payload=payload)

    def update(self, service_id, payload):
        path = '%s/%s' % (self.services_path, service_id)

        return self.request('PUT', path, payload=payload)

    def remove(self, service_id):
        path = '%s/%s' % (self.services_path, service_id)

        return self.request('DELETE', path)


class ConfigurationClient(BaseClient):
    def __init__(self, base_url, auth_headers):
        super(ConfigurationClient, self).__init__(base_url, auth_headers)
        self.configuration_path = '/configuration'

    def list(self):
        return self.request('GET', self.configuration_path)

    def get(self, configuration_id):
        path = '%s/%s' % (self.configuration_path, configuration_id)

        return self.request('GET', path)

    def set(self, configuration_id, value):
        path = '%s/%s' % (self.configuration_path, configuration_id)
        payload = {'value': value}

        return self.request('PUT', path, payload=payload)

    def remove(self, configuration_id):
        path = '%s/%s' % (self.configuration_path, configuration_id)

        return self.request('DELETE', path)


class AccountClient(BaseClient):
    def __init__(self, base_url, auth_headers):
        super(AccountClient, self).__init__(base_url, auth_headers)
        self.limits_path = '/limits'

    def get_limits(self):
        return self.request('GET', self.limits_path)


class Client(object):
    """
    The main client to be instantiated by the user.
    """
    def __init__(self, username, api_key,
                 base_url=DEFAULT_API_URL, region='us'):
        """
        @param username: Rackspace username.
        @type username: C{str}
        @param api_key: Rackspace API key.
        @type api_key: C{str}
        @param base_url: The base Cloud Registry URL.
        @type base_url: C{str}
        @param region: Rackspace region.
        @type region: C{str}
        """
        auth_url = DEFAULT_AUTH_URLS.get(region, 'us')

        if not auth_url.endswith('/'):
            auth_url += '/'

        self.username = username
        self.api_key = api_key
        self.auth_headers = self._authenticate()
        self.base_url = base_url
        self.sessions = SessionsClient(self.base_url, self.auth_headers)
        #self.events = EventsClient(self.base_url)
        #self.services = ServicesClient(self.base_url)
        #self.configuration = ConfigurationClient(self.base_url)
        #self.account = AccountClient(self.base_url)

    def _authenticate(self):
        try:
            driver = RackspaceNodeDriver(self.username, self.api_key)
            driver.connection._populate_hosts_and_request_paths()
            auth_token = driver.connection.auth_token
            tenant_id = driver.connection.request_path.split('/')[-1]
            return {'X-Auth-Token': auth_token,
                    'X-Tenant-Id': tenant_id}
        except (InvalidCredsError, MalformedResponseError):
            raise Exception('The username or password you entered is ' +
                            'incorrect. Please try again.')


c = Client('shawnps', 'b9fc192f142495902031de738a36edcb')
print c.sessions.list()
