# Copyright 2013 Rackspace Hosting, Inc.
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

__all__ = [
    'Client',
    'ServicesClient',
    'EventsClient',
    'ConfigurationClient',
    'AccountClient'
]

from copy import deepcopy
from time import sleep

from constants import DEFAULT_API_URL, MAX_HEARTBEAT_TIMEOUT
from base import BaseClient
from heartbeater import HeartBeater
from errors import ValidationError


class EventsClient(BaseClient):
    def __init__(self, base_url, username, api_key, region):
        super(EventsClient, self).__init__(base_url, username,
                                           api_key, region)
        self.events_path = '/events'

    def list(self, marker=None, limit=None):
        options = self._get_options_object(marker=marker, limit=limit)
        return self.request('GET', self.events_path, options=options)


class ServicesClient(BaseClient):
    def __init__(self, base_url, username, api_key, region):
        super(ServicesClient, self).__init__(base_url, username,
                                             api_key, region)
        self.services_path = '/services'

    def list(self, marker=None, limit=None):
        options = self._get_options_object(marker=marker, limit=limit)
        return self.request('GET', self.services_path, options=options)

    def list_for_tag(self, tag, marker=None, limit=None):
        options = self._get_options_object(marker=marker, limit=limit)
        options['tag'] = tag

        return self.request('GET', self.services_path, options=options)

    def get(self, service_id):
        path = '%s/%s' % (self.services_path, service_id)

        return self.request('GET', path)

    def create(self, service_id, heartbeat_timeout, payload=None):
        payload = deepcopy(payload) if payload else {}
        payload['id'] = service_id
        payload['heartbeat_timeout'] = heartbeat_timeout

        heartbeater = HeartBeater(self.base_url,
                                  self.username,
                                  self.api_key,
                                  self.region,
                                  None,
                                  heartbeat_timeout)

        return self.request('POST', self.services_path, payload=payload,
                            heartbeater=heartbeater)

    def heartbeat(self, service_id, token):
        path = '%s/%s/heartbeat' % (self.services_path, service_id)
        payload = {'token': token}

        return self.request('POST', path, payload=payload)

    def update(self, service_id, payload):
        path = '%s/%s' % (self.services_path, service_id)

        return self.request('PUT', path, payload=payload)

    def remove(self, service_id):
        path = '%s/%s' % (self.services_path, service_id)

        return self.request('DELETE', path)

    def register(self, service_id, heartbeat_timeout, payload=None,
                 retry_delay=2):
        retry_count = MAX_HEARTBEAT_TIMEOUT / retry_delay
        success = False
        retry_counter = 0
        last_err = None
        result = None

        def do_register(success, result, retry_counter, last_err):
            if success and (retry_counter < retry_count):
                return result

            elif (not success) and (retry_counter == retry_count):
                return last_err
            try:
                result = self.create(service_id=service_id,
                                     heartbeat_timeout=heartbeat_timeout,
                                     payload=payload)
                success = True

                return do_register(success, result, retry_counter, last_err)
            except ValidationError as e:
                last_err = e.args[0]
                if last_err.type == 'serviceWithThisIdExists':
                    retry_counter += 1
                    sleep(retry_delay)

                    return do_register(success, result, retry_counter,
                                       last_err)
                else:
                    return last_err

        return do_register(success, result, retry_counter, last_err)


class ConfigurationClient(BaseClient):
    def __init__(self, base_url, username, api_key, region):
        super(ConfigurationClient, self).__init__(base_url, username,
                                                  api_key, region)
        self.configuration_path = '/configuration'

    def list(self, marker=None, limit=None):
        options = self._get_options_object(marker=marker, limit=limit)
        return self.request('GET', self.configuration_path, options=options)

    def list_for_namespace(self, namespace, marker=None, limit=None):
        options = self._get_options_object(marker=marker, limit=limit)

        if namespace[0] != '/':
            namespace = '/%s' % (namespace)

        if namespace[len(namespace) - 1] != '/':
            namespace += '/'

        path = '%s%s' % (self.configuration_path, namespace)

        return self.request('GET', path, options=options)

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

        self.services = ServicesClient(self.base_url, self.username,
                                       self.api_key, self.region)
        self.events = EventsClient(self.base_url, self.username,
                                   self.api_key, self.region)
        self.configuration = ConfigurationClient(self.base_url,
                                                 self.username,
                                                 self.api_key,
                                                 self.region)
        self.account = AccountClient(self.base_url, self.username,
                                     self.api_key, self.region)
