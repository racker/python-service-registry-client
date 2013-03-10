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

import httplib

US_AUTH_URL = 'https://identity.api.rackspacecloud.com/v2.0/tokens'
UK_AUTH_URL = 'https://lon.identity.api.rackspacecloud.com/v2.0/tokens'
DEFAULT_AUTH_URLS = {'us': US_AUTH_URL,
                     'uk': UK_AUTH_URL}
DEFAULT_API_URL = 'https://dfw.registry.api.rackspacecloud.com/v1.0/'
MAX_HEARTBEAT_TIMEOUT = 120
MAX_401_RETRIES = 1


ACCEPTABLE_STATUS_CODES = {'GET': (httplib.OK,),
                           'POST': (httplib.OK, httplib.CREATED),
                           'PUT': (httplib.NO_CONTENT,),
                           'DELETE': (httplib.NO_CONTENT,)}
