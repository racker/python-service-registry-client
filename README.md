# Python Rackspace Service Registry client

A Python client for Rackspace Service Registry.

# License

This library is distributed under the [Apache license](http://www.apache.org/licenses/LICENSE-2.0.html).

# Usage

```Python
from service_registry.client import Client

RACKSPACE_USERNAME = 'username'
RACKSPACE_KEY = 'api key'

client = Client(RACKSPACE_USERNAME, RACKSPACE_KEY)
```

## Services

Create a service with a heartbeat timeout of 10:

```Python
service_id = 'my-service-1'
payload = {'metadata': {'key': 'value'}}
heartbeat_timeout = 10

client.services.create(service_id, heartbeat_timeout, payload)
```

Heartbeat a service:

```Python
service_id = 'my-service-1'
token = 'returned-heartbeat-token'

client.services.heartbeat(service_id, token)
```
