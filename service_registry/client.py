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
try:
        import simplejson as json
except:
        import json

from datetime import datetime
from dateutil import parser
import libcloud.security
from libcloud.common.types import InvalidCredsError, MalformedResponseError
from libcloud.compute.drivers.rackspace import RackspaceNodeDriver
import random
import requests
from time import sleep, mktime

libcloud.security.VERIFY_SSL_CERT = False

US_AUTH_URL = 'https://identity.api.rackspacecloud.com/v2.0/tokens'
UK_AUTH_URL = 'https://lon.identity.api.rackspacecloud.com/v2.0/tokens'
DEFAULT_AUTH_URLS = {'us': US_AUTH_URL,
                     'uk': UK_AUTH_URL}
DEFAULT_API_URL = 'https://csr-staging.rax.io/v1.0/'


class BaseClient(object):
    def __init__(self, base_url, username, api_key, region):
        self.base_url = base_url
        self.username = username
        self.api_key = api_key
        self.auth_headers = None
        self.auth_token_expires = None
        self.region = region

        auth_url = DEFAULT_AUTH_URLS.get(region, 'us')

        if not auth_url.endswith('/'):
            auth_url += '/'

        self.auth_url = auth_url

    def get_id_from_url(self, url):
        return url.split('/')[-1]

    def request(self, method, path, options=None,
                payload=None, heartbeater=None):
        self.auth_headers = self._authenticate()
        tenant_id = self.auth_headers['X-Tenant-Id']
        request_url = self.base_url + tenant_id + path
        if method == 'GET':
            r = requests.get(request_url,
                             headers=self.auth_headers,
                             params=options)
            return r.json
        elif method == 'POST':
            r = requests.post(request_url, headers=self.auth_headers,
                              data=json.dumps(payload))

            if 'heartbeat' in path:
                return r.json

            id_from_url = self.get_id_from_url(r.headers['location'])

            if 'services' in path:
                return id_from_url

            heartbeater.session_id = id_from_url
            heartbeater.next_token = r.json['token']

            return r.json, id_from_url, heartbeater

    def _authenticate(self):
        if self.auth_headers:
            current_time = datetime.now()
            unix_current_time = mktime(current_time.timetuple())
            if self.auth_token_expires and \
                    self.auth_token_expires < unix_current_time:
                        return self.auth_headers
        try:
            driver = RackspaceNodeDriver(self.username, self.api_key,
                                         ex_force_auth_url=self.auth_url,
                                         ex_force_version='2.0',
                                         ex_force_service_region=self.region)
            driver.connection._populate_hosts_and_request_paths()
            auth_token = driver.connection.auth_token
            tenant_id = driver.connection.request_path.split('/')[-1]
            expires = driver.connection.auth_token_expires
            expires_datetime = parser.parse(expires)
            self.auth_token_expires = \
                mktime(expires_datetime.timetuple())
            return {'X-Auth-Token': auth_token,
                    'X-Tenant-Id': tenant_id}
        except (InvalidCredsError, MalformedResponseError):
            raise Exception('The username or password you entered is ' +
                            'incorrect. Please try again.')


class SessionsClient(BaseClient):
    def __init__(self, base_url, username, api_key, region):
        super(SessionsClient, self).__init__(base_url, username,
                                             api_key, region)
        self.sessions_path = '/sessions'
        self.base_url = base_url
        self.username = username
        self.api_key = api_key
        self.region = region

    def create(self, heartbeat_timeout, payload=None):
        path = self.sessions_path
        payload = deepcopy(payload) if payload else {}
        payload['heartbeat_timeout'] = heartbeat_timeout

        heartbeater = HeartBeater(self.base_url,
                                  self.username,
                                  self.api_key,
                                  self.region,
                                  None,
                                  heartbeat_timeout)

        return self.request('POST',
                            path,
                            payload=payload,
                            heartbeater=heartbeater)

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
    def __init__(self, base_url, username, api_key, region):
        super(EventsClient, self).__init__(base_url, username,
                                           api_key, region)
        self.events_path = '/events'

    def list(self, marker=None):
        options = None
        if marker:
            options = {'marker': marker}

        return self.request('GET', self.events_path, options=options)


class ServicesClient(BaseClient):
    def __init__(self, base_url, username, api_key, region):
        super(ServicesClient, self).__init__(base_url, username,
                                             api_key, region)
        self.services_path = '/services'

    def list(self):
        return self.request('GET', self.services_path)

    def list_for_tag(self, tag):
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
    def __init__(self, base_url, username, api_key, region):
        super(ConfigurationClient, self).__init__(base_url, username,
                                                  api_key, region)
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
    def __init__(self, base_url, username, api_key, region):
        super(AccountClient, self).__init__(base_url, username,
                                            api_key, region)
        self.limits_path = '/limits'

    def get_limits(self):
        return self.request('GET', self.limits_path)


class HeartBeater(BaseClient):
    def __init__(self, base_url, username, api_key, region,
                 session_id, heartbeat_timeout):
        """
        HeartBeater will start heartbeating a session once start() is called,
        and stop heartbeating the session when stop() is called.

        @param base_url:  The base Cloud Registry URL.
        @type base_url: C{str}
        @param username: Rackspace username.
        @type username: C{str}
        @param api_key: Rackspace API key.
        @type api_key: C{str}
        @param session_id: The ID of the session to heartbeat.
        @type session_id: C{str}
        @param heartbeat_timeout: The amount of time after which a session will
        time out if a heartbeat is not received.
        @type heartbeat_timeout: C{int}
        """
        super(HeartBeater, self).__init__(base_url, username, api_key, region)
        self.session_id = session_id
        self.heartbeat_timeout = heartbeat_timeout
        self.heartbeat_interval = self._calculate_interval(heartbeat_timeout)
        self.next_token = None
        self._stopped = False

    def _calculate_interval(self, heartbeat_timeout):
        if heartbeat_timeout < 15:
            return heartbeat_timeout * 0.6
        else:
            return heartbeat_timeout * 0.8

    def _start_heartbeating(self):
        path = '/sessions/%s/heartbeat' % self.session_id
        payload = {'token': self.next_token}

        if self._stopped:
            return

        interval = self.heartbeat_interval

        if interval > 5:
            interval = interval + random.randrange(-3, 1)

        sleep(interval)

        result = self.request('POST', path, payload=payload)

        self.next_token = result['token']

        self._start_heartbeating()

    def start(self):
        """
        Start heartbeating the session. Will continue to heartbeat
        until stop() is called.
        """
        return self._start_heartbeating()

    def stop(self):
        """
        Stop heartbeating the session.
        """
        self._stopped = True


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
        self.username = username
        self.api_key = api_key
        self.base_url = base_url
        self.region = region
        self.sessions = SessionsClient(self.base_url, self.username,
                                       self.api_key, self.region)
        self.events = EventsClient(self.base_url, self.username,
                                   self.api_key, self.region)
        self.services = ServicesClient(self.base_url, self.username,
                                       self.api_key, self.region)
        self.configuration = ConfigurationClient(self.base_url,
                                                 self.username,
                                                 self.api_key,
                                                 self.region)
        self.account = AccountClient(self.base_url, self.username,
                                     self.api_key, self.region)