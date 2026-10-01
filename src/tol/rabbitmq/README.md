<!--
SPDX-FileCopyrightText: 2026 Genome Research Ltd.

SPDX-License-Identifier: MIT
-->

# tol.rabbitmq — the ToL message bus

A thin layer over RabbitMQ (pika, blocking) for publishing and consuming
messages between ToL applications and processes.

- **Publishers** write `bus_message` objects through a `RabbitmqDataSource`,
  either directly in Python or over HTTP via `data_blueprint`.
- **Consumers** are per-app processes that declare their own queue and
  dispatch messages to handlers by `envelope.type`.
- The broker does the routing. There is no central router process.

## Topology

| Thing                | Name                    | Notes                         |
| -------------------- | ----------------------- | ----------------------------- |
| Exchange             | `tol` (topic)           | `RABBITMQ_EXCHANGE`           |
| Dead-letter exchange | `tol.dlx`               | `RABBITMQ_DLX`                |
| App queue            | `<app>.<category>`      | e.g. `portal.notify`; quorum  |
| Binding              | `<category>.<app>.#`    | declared by `create_consumer` |
| Dead queue           | `<app>.<category>.dead` | quorum, `x-max-length` 10000  |

All queues are quorum queues (RabbitMQ 4.x). App queues also set:

- `x-delivery-limit` 5 (`QueueSpec.delivery_limit`). This caps
  redeliveries of a message that keeps killing its consumer before the
  ack. Once the limit is reached, the message is dead-lettered.
- `x-dead-letter-strategy: at-least-once`, so a dead-lettered message is
  not lost if the dead queue is briefly unavailable. This requires
  `x-overflow: reject-publish`.

Routing keys are `<category>.<app>.<subtype>[.<more>]`: at least three
dot-separated words of `[a-z0-9_-]`, with no wildcards. Examples:
`notify.portal.sample_received`, `notify.genome-notes.published`.

Publishers declare only the exchanges. Queues are declared by the consumer
that owns them, so **start the consumer before publishing to it**. A
message whose routing key matches no queue is rejected (see _Publishing_),
not silently dropped.

Queue arguments cannot be changed on an existing queue: redeclaring with
different arguments fails with `PRECONDITION_FAILED`. In dev, run
`docker compose down -v`.

## Message envelope

Every message body is a `MessageEnvelope`:

```json
{
  "id": "V1StGXR8_Z5jdHi6B-myT",
  "version": 1,
  "type": "notification",
  "source": "portal",
  "created_at": "2026-09-29T12:00:00Z",
  "correlation_id": null,
  "context": {}
}
```

- `id` is the message id and must equal the `bus_message` object id.
- `type` selects the consumer handler.
- `context` is owned by that handler.
- `created_at` must be timezone-aware.

For `type == "notification"`, `context` is a full `NotificationRequest`.
Use `wrap_in_envelope(request, source)` to build it.

## Publishing

### Python

```python
from tol.rabbitmq import (
    NotificationRequest, RabbitmqConfig, create_rabbitmq_datasource,
    generate_unique_id, wrap_in_envelope,
)

ds = create_rabbitmq_datasource(RabbitmqConfig.from_env())

request = NotificationRequest(
    id=generate_unique_id(),
    channels=['email'],
    type='sample_received',
    recipients=[{'email': 'someone@sanger.ac.uk'}],
    context={'sample_id': 'S123'},
)
message = ds.data_object_factory(
    'bus_message',
    id_=request.id,
    attributes={
        'body': wrap_in_envelope(request, source='portal').model_dump(mode='json'),
        'routing_key': 'notify.portal.sample_received',
    },
)
ds.insert_batch('bus_message', [message])
```

### HTTP

Mount the generic data blueprint:

```python
from tol.api_base import data_blueprint

app.register_blueprint(data_blueprint(rabbitmq_ds), url_prefix='/api/v1')
```

Then send a JSON:API insert to `POST /api/v1/data/bus_message:insert`:

```json
{
  "data": [
    {
      "type": "bus_message",
      "id": "<envelope id>",
      "attributes": {
        "body": { "...": "envelope" },
        "routing_key": "notify.portal.sample_received"
      }
    }
  ]
}
```

Guard `INSERT` on this blueprint with an `auth_inspector` in production.
Otherwise it is an open relay: messages carry recipients and content.

### Guarantees and errors

Each batch is validated in full before anything is published. Publishing
uses publisher confirms and `mandatory=True`.

| Failure                                                | Status |
| ------------------------------------------------------ | ------ |
| Bad routing key, invalid envelope/request, id mismatch | 400    |
| No queue bound for the routing key (unroutable)        | 422    |
| Any other broker error                                 | 500    |

## Consuming

```python
from tol.rabbitmq import (
    NotificationChannel, RabbitmqConfig, create_consumer, notification_handler,
)

consumer = create_consumer(
    RabbitmqConfig.from_env(),          # needs RABBITMQ_APP_NAME
    handlers={
        'notification': notification_handler({
            NotificationChannel.EMAIL: send_email,
        }),
    },
    category='notify',
)
consumer.start()                        # blocks; SIGINT/SIGTERM stop cleanly
```

`python -m tol.rabbitmq` runs a log-only example consumer.

- `create_consumer` validates `app_name` and `category` against
  `^[a-z0-9_-]+$`, declares the queue, the binding and the dead queue, and
  connects eagerly. A topology error fails at startup.
- `prefetch_count=1`: one message in flight per consumer process. Scale by
  running more processes.
- Handler outcome:
  - It returns: the message is **acked**.
  - It raises, the envelope is invalid, or there is no handler for `type`:
    the message is **nacked without requeue** and goes to the dead queue.
- `notification_handler` fans a request out into one `NotificationDelivery`
  per (channel, recipient) pair. If any requested channel has no
  dispatcher, it raises before dispatching anything.
- SIGINT/SIGTERM let the in-flight handler finish and ack, then the
  connection closes.

### At-least-once delivery: handlers MUST be idempotent

A message can be delivered more than once:

- when the process dies after the handler runs but before the ack;
- on every replay from a dead queue.

Replays re-run _every_ delivery in a notification, including the ones that
already succeeded. For example, if email succeeded and Slack raised, a
replay sends the email again.

Dedupe on `envelope.id` (handlers) or `delivery_id` (dispatchers).
`delivery_id` is deterministic: `<notification id>:<channel>:<recipient index>`.

## Deployment

- Run consumers under a **restarting supervisor** (k8s Deployment, or
  compose `restart: unless-stopped`). The initial connection is retried
  (`RABBITMQ_CONNECTION_ATTEMPTS`). A connection lost while consuming exits
  the process, and the supervisor restarts it. There is no in-process
  reconnect loop.
- Set `terminationGracePeriodSeconds` longer than your slowest handler.
  60s covers the email sender's 30s SMTP timeout.
- A handler blocks heartbeats while it runs. Keep handlers well under
  `RABBITMQ_HEARTBEAT`.

### Broker setup (staging/production)

- Ops own the exchanges `tol` and `tol.dlx` and create them from the
  broker definitions file. Apps run with `RABBITMQ_DECLARE_EXCHANGES=false`,
  so the SDK only checks passively that the exchanges exist; if one is
  missing, the app fails at startup.
- Create one broker user per app per vhost (`staging`, `production`),
  with these permissions:

| Permission | Pattern                        |
| ---------- | ------------------------------ |
| configure  | `^<app>\..*$`                  |
| write      | `^(tol\|tol\.dlx\|<app>\..*)$` |
| read       | `^(tol\|tol\.dlx\|<app>\..*)$` |

- Alert when any `*.dead` queue has a depth greater than 0.

## Environment variables

Prefix `RABBITMQ_` (change it via `RabbitmqConfig.from_env(prefix=...)`).

| Variable                     | Default      | Notes                                                   |
| ---------------------------- | ------------ | ------------------------------------------------------- |
| `HOST`                       | **required** |                                                         |
| `USERNAME`                   | **required** |                                                         |
| `PASSWORD`                   | **required** |                                                         |
| `PORT`                       | `5672`       |                                                         |
| `VHOST`                      | `/`          |                                                         |
| `EXCHANGE`                   | `tol`        |                                                         |
| `DLX`                        | `tol.dlx`    |                                                         |
| `DECLARE_EXCHANGES`          | `true`       | `false` in staging/prod: exchanges are ops-owned        |
| `APP_NAME`                   | `''`         | required by `create_consumer`; stamped as AMQP `app_id` |
| `USE_SSL`                    | `false`      |                                                         |
| `CA_FILE`                    | unset        | CA bundle for an internal CA                            |
| `WRITE_BATCH_SIZE`           | `100`        |                                                         |
| `HEARTBEAT`                  | `60`         | seconds                                                 |
| `BLOCKED_CONNECTION_TIMEOUT` | `30`         | seconds                                                 |
| `SOCKET_TIMEOUT`             | `10`         | seconds                                                 |
| `CONNECTION_ATTEMPTS`        | `3`          |                                                         |
| `RETRY_DELAY`                | `2`          | seconds                                                 |

`RABBITMQ_MANAGEMENT_URL` is read only by the integration and system test
helpers. The SDK itself does not use it.
