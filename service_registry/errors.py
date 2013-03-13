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
    'ValidationError',
    'APIError',
    'InvalidCredentialsError'
]


class ValidationError(Exception):
    def __init__(self, type, code, message, txnId, details):
        self.type = type
        self.code = code
        self.message = message
        self.txnId = txnId or 'unknown'
        self.details = details

    def __str__(self):
        return ('<ValidationError type=%s, code=%s, txnId=%s, '
                'message=%s, details=%s' %
                (self.type, self.code, self.txnId, self.message, self.details))

    pass


class APIError(Exception):
    pass


class InvalidCredentialsError(APIError):
    pass
