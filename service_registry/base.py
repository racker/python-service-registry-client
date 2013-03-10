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
    'BaseClient'
]

import httplib
import requests

from time import mktime, time

try:
    import simplejson as json
except:
    import json

from dateutil import parser
from libcloud.common.types import InvalidCredsError, MalformedResponseError
from libcloud.compute.drivers.rackspace import RackspaceNodeDriver

from constants import DEFAULT_AUTH_URLS
from constants import MAX_401_RETRIES
from constants import ACCEPTABLE_STATUS_CODES
from errors import (APIError, ValidationError, InvalidCredentialsError)


class BaseClient(object):
    def __init__(self, base_url, username, api_key, region):
        self.base_url = base_url
        self.username = username
        self.api_key = api_key
        self.auth_headers = None
        self.auth_token_expires = None
        self.region = region

        valid_regions = DEFAULT_AUTH_URLS.keys()
        if region not in valid_regions:
            raise ValueError('Invalid region %s. Valid regions are: %s' % (
                             region, ', '.join(valid_regions)))

        auth_url = DEFAULT_AUTH_URLS[region]

        if not auth_url.endswith('/'):
            auth_url += '/'

        self.auth_url = auth_url

    def get_id_from_url(self, url):
        return url.split('/')[-1]

    def _get_options_object(self, marker=None, limit=None):
        options = {}

        if marker:
            options['marker'] = marker

        if limit:
            options['limit'] = limit

        return options

    def request(self, method, path, options=None, payload=None,
                heartbeater=None, re_authenticate=False, retry_count=0):
        self.auth_headers = self._authenticate(force=re_authenticate)
        tenant_id = self.auth_headers['X-Tenant-Id']
        request_url = self.base_url + tenant_id + path

        if method not in ['GET', 'POST', 'PUT', 'DELETE']:
            raise ValueError('Invalid method: %s' % (method))

        data = json.dumps(payload) if payload else None
        request_kwargs = {'method': method.lower(), 'url': request_url,
                          'headers': self.auth_headers, 'params': options,
                          'data': data}

        if retry_count < MAX_401_RETRIES:
            retry_count += 1
            r = requests.request(**request_kwargs)

            if r.status_code == httplib.UNAUTHORIZED:
                return self.request(method=method, path=path, options=options,
                                    payload=payload, heartbeater=heartbeater,
                                    re_authenticate=True,
                                    retry_count=retry_count)
        else:
            raise APIError('API returned 401')

        def _check_status_code(status_code, method):
            if status_code not in ACCEPTABLE_STATUS_CODES[method]:
                data = r.json()
                raise ValidationError(type=data['type'], code=data['code'],
                                      message=data['message'],
                                      txnId=data.get('txnId', None),
                                      details=data['details'])

        if method == 'GET':
            _check_status_code(r.status_code, 'GET')

            return r.json()
        elif method == 'POST':
            if int(r.headers.get('content-length', 0)) > 0:
                data = r.json()
            else:
                data = None

            _check_status_code(r.status_code, 'POST')

            if 'heartbeat' in path:
                return data

            id_from_url = self.get_id_from_url(r.headers['location'])

            heartbeater.service_id = id_from_url
            heartbeater.next_token = data['token']

            return data, heartbeater
        elif method == 'PUT':
            _check_status_code(r.status_code, 'PUT')

            return True
        elif method == 'DELETE':
            _check_status_code(r.status_code, 'DELETE')

            return True

    def _authenticate(self, force=False):
        if self.auth_headers:
            current_time = time()
            if not force and (self.auth_token_expires and
                             (self.auth_token_expires < current_time)):
                return self.auth_headers
        try:
            driver = RackspaceNodeDriver(self.username, self.api_key,
                                         ex_force_auth_url=self.auth_url,
                                         ex_force_auth_version='2.0',
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
            raise InvalidCredentialsError('The username or password you'
                                          ' entered is incorrect. Please'
                                          ' try again.')
