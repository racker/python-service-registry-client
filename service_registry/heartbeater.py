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
    'HeartBeater'
]

import random
from time import sleep

from base import BaseClient


class HeartBeater(BaseClient):
    def __init__(self, base_url, username, api_key, region,
                 service_id, heartbeat_timeout):
        """
        HeartBeater will start heartbeating a service once start() is called,
        and stop heartbeating it when stop() is called.

        @param base_url:  The base Cloud Registry URL.
        @type base_url: C{str}
        @param username: Rackspace username.
        @type username: C{str}
        @param api_key: Rackspace API key.
        @type api_key: C{str}
        @param service_id: The ID of the service to heartbeat.
        @type service_id: C{str}
        @param heartbeat_timeout: The amount of time after which a service will
        time out if a heartbeat is not received.
        @type heartbeat_timeout: C{int}
        """
        super(HeartBeater, self).__init__(base_url, username, api_key, region)
        self.service_id = service_id
        self.heartbeat_timeout = heartbeat_timeout
        self.heartbeat_interval = self._calculate_interval(heartbeat_timeout)
        self.next_token = None
        self._stopped = False

    def _calculate_interval(self, heartbeat_timeout):
        if heartbeat_timeout < 15:
            return (heartbeat_timeout * 0.6)
        else:
            return (heartbeat_timeout * 0.8)

    def _start_heartbeating(self):
        path = '/services/%s/heartbeat' % (self.service_id)
        payload = {'token': self.next_token}

        if self._stopped:
            return

        interval = self.heartbeat_interval

        if interval > 5:
            interval = (interval + random.randrange(-3, 1))

        sleep(interval)

        result = self.request('POST', path, payload=payload)
        self.next_token = result['token']

        self._start_heartbeating()

    def start(self):
        """
        Start heartbeating the service. Will continue to heartbeat
        until stop() is called.
        """
        return self._start_heartbeating()

    def stop(self):
        """
        Stop heartbeating the service.
        """
        self._stopped = True
