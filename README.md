# Python Rackspace Service Registry client

A Python client for Rackspace Service Registry.

# License

This library is distributed under the [Apache license](http://www.apache.org/licenses/LICENSE-2.0.html).

# Usage

```Python
from service_registry import Client

RACKSPACE_USERNAME = 'username'
RACKSPACE_KEY = 'api key'

client = Client(RACKSPACE_USERNAME, RACKSPACE_KEY)
```

## Sessions

Create a session with a heartbeat timeout of 10:

```Python
# Optional metadata (must contain string keys and values, up to 255 chars)
options = {'key': 'value'}
heartbeat_timeout = 10

client.sessions.create(heartbeat_timeout, options)
```

List sessions:

```Python
client.sessions.list()
```

Get session:

```Python
session_id = 'seFoo'

client.sessions.get(session_id)
```

Heartbeat a session:

```Python
session_id = 'seFoo'
token = 'token'

client.sessions.heartbeat(session_id, token)
```

Update existing session:

```Python
session_id = 'seFoo'
payload = {'heartbeat_timeout': 15}

client.sessions.update(session_id, payload)
```

## Events

List events:

```Python
marker = 'last-seen-token'

client.events.list(marker)
```

## Services

List services:

```Python

client.services.list()
```

List services for a specific tag:

```Python
tag = 'tag'

client.services.list_for_tag(tag)
```

Get service by ID:

```Python
service_id = 'messenger1'

client.services.get(service_id)
```

Create a new service:

```Python
session_id = 'session_id'
service_id = 'messenger1'
payload = {
    'tags': ['messenger', 'stats'],
    'metadata': {'someKey': 'someValue', 'anotherKey': 'anotherValue'}
}

client.services.register(session_id, service_id, payload)
```

Update existing service:

```Python
service_id = 'messenger1'
payload = {
    'tags': ['tag1', 'tag2'],
    'metadata': {'aKey': 'aValue'}
}

client.services.update(service_id, payload)
```

## Configuration

List configuration values:

```Python

client.configuration.list()
```

Get configuration value by id:

```Python
configuration_id = 'configId'

client.configuration.get(configuration_id)
```

Update configuration value:

```Python
configuration_id = 'configId'
value = 'new-value'

client.configuration.set(configuration_id, value)
```

Delete configuration value:

```Python
configuration_id = 'configId'

client.configuration.remove(configuration_id)
```

## Accounts

Get account limits:

```Python
client.account.get_limits()
```
