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

| Thing                | Name                    | Notes                        |
| -------------------- | ----------------------- | ---------------------------- |
| Exchange             | `tol` (topic)           | `RABBITMQ_EXCHANGE`          |
| Dead-letter exchange | `tol.dlx`               | `RABBITMQ_DLX`               |
| App queue            | `<app>.<category>`      | e.g. `portal.notify`; quorum |
| Binding              | `<category>.<app>.#`    | declared by `consume()`      |
| Dead queue           | `<app>.<category>.dead` | quorum, `x-max-length` 10000 |

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

Every message body on the wire is a `MessageEnvelope`. `RabbitmqDataSource`
builds it from the `bus_message` attributes; publishers never do:

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

- `id` is the `bus_message` object id, generated if the object has none.
- `type` is the `message_type` attribute and selects the consumer handler.
- `source` (the publisher's `RABBITMQ_APP_NAME`) and `created_at` are
  stamped by the datasource. A caller-supplied `source` is ignored.
- `context` is owned by the handler.

For `type == "notification"`, `context` is a full `NotificationRequest`.

## Publishing

| Attribute        | Default                 | Notes                                    |
| ---------------- | ----------------------- | ---------------------------------------- |
| `message_type`   | **required**            | lowercase words, dot-separated allowed   |
| `context`        | `{}`                    | handler-owned payload                    |
| `target_app`     | own `RABBITMQ_APP_NAME` | the app whose queue receives the message |
| `category`       | `notify`                |                                          |
| `correlation_id` | unset                   |                                          |
| `headers`        | unset                   | AMQP headers                             |

The datasource derives the routing key
`<category>.<target_app>.<message_type>`.

### Python

```python
from tol.rabbitmq import RabbitmqConfig, create_rabbitmq_datasource

ds = create_rabbitmq_datasource(RabbitmqConfig.from_env())  # needs RABBITMQ_APP_NAME

message = ds.data_object_factory(
    'bus_message',
    attributes={
        'message_type': 'sample_received',
        'context': {'sample_id': 'S123'},
        'target_app': 'portal',
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
      "attributes": {
        "message_type": "sample_received",
        "context": { "sample_id": "S123" },
        "target_app": "portal"
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

| Failure                                                          | Status |
| ---------------------------------------------------------------- | ------ |
| Invalid `message_type`/`target_app`/`category`/`context`/request | 400    |
| No queue bound for the routing key (unroutable)                  | 422    |
| Any other broker error                                           | 500    |

## Consuming

`RabbitmqDataSource` is a `Consumer`. Handlers are specified like pipeline
steps: one `{module, class_name, config_details}` spec per message type.

```python
from tol.rabbitmq import RabbitmqConfig, create_rabbitmq_datasource

ds = create_rabbitmq_datasource(RabbitmqConfig.from_env())  # needs RABBITMQ_APP_NAME
ds.consume({
    'sample.received': {
        'module': 'main.handlers',
        'class_name': 'SampleReceivedHandler',
        'config_details': {'extra_info': 'some_value'},
    },
})                                      # blocks; SIGINT/SIGTERM stop cleanly
```

A handler subclasses `tol.core.Handler`, declares a nested `Config`
dataclass and implements `handle(obj)`:

```python
from dataclasses import dataclass

from tol.core import DataObject, Handler


class SampleReceivedHandler(Handler):
    @dataclass(frozen=True, kw_only=True)
    class Config:
        extra_info: str

    def __init__(self, config: Config, data_object_factory, **kwargs):
        self.__config = config

    def handle(self, obj: DataObject) -> None:
        ...  # obj is an `output_message`
```

An `output_message` has `message_type`, `version`, `context`, `source`,
`created_at`, `correlation_id`, `routing_key` and `redelivered`; its id is
the envelope id.

- `consume(handlers, category='notify')` consumes `<app>.<category>`,
  bound to `<category>.<app>.#`. It validates `category`, builds every
  handler, declares the queue, the binding and the dead queue, and connects
  before consuming. A bad spec or topology error fails at startup.
- `prefetch_count=1`: one message in flight per consumer process. Scale by
  running more processes.
- Handler outcome:
  - It returns: the message is **acked**.
  - It raises, the envelope is invalid, or there is no handler for its
    `message_type`: the message is **nacked without requeue** and goes to
    the dead queue.
- `NotificationHandler` fans a `notification` request out into one
  `NotificationDelivery` per (channel, recipient) pair. Its `channels`
  config maps each channel to a `Dispatcher` spec. If any requested channel
  has no dispatcher, it raises before dispatching anything.
- SIGINT/SIGTERM let the in-flight handler finish and ack, then the
  connection closes.

### At-least-once delivery: handlers MUST be idempotent

A message can be delivered more than once:

- when the process dies after the handler runs but before the ack;
- on every replay from a dead queue.

Replays re-run _every_ delivery in a notification, including the ones that
already succeeded. For example, if email succeeded and Slack raised, a
replay sends the email again.

Dedupe on `obj.id` (handlers) or `delivery_id` (dispatchers).
`delivery_id` is deterministic: `<notification id>:<channel>:<recipient index>`.

## Email

```python
ds.consume({
    'notification': {
        'module': 'tol.rabbitmq.handlers',
        'class_name': 'NotificationHandler',
        'config_details': {'channels': {
            'email': {
                'module': 'tol.rabbitmq.dispatchers',
                'class_name': 'EmailDispatcher',
                'config_details': {'template_dirs': ['templates/email']},
            },
        }},
    },
})
```

`EmailDispatcher` reads SMTP settings from the `SMTP_*` environment.

- **Templates.** The notification `type` names the template pair:
  `<type>.subject.txt` and `<type>.body.html`. App directories are
  searched in order, then the SDK's own templates.
- **Branding.** Extend `tol_base.html` (blocks `title`, `header`,
  `content`, `footer`). A custom-branded app shadows it by putting its own
  `tol_base.html` in its template directory.
- **Template context** is the request `context` plus `recipient`.
  `recipient` is reserved: it overrides any context key of the same name.
- **Escaping.** The body is HTML-escaped. The subject is not escaped, and
  its whitespace (including newlines) is collapsed to single spaces.
- **One email per recipient,** so recipients never see each other's
  addresses.
- **Failures go to the dead queue:** a missing template variable, an
  unknown `type`, or any SMTP error. There is no automatic retry yet.
- `tol.notify` does not depend on the bus. Send directly with
  `EmailSender.send(to, subject, html_body, text_body=None)`.

**Do not run a production email consumer until handler idempotency
lands.** Until then, a replay re-sends every email in the notification.

Locally, the compose stack runs mailpit. Every email sent in tests is
captured and viewable at http://localhost:8025.

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

| Variable                     | Default      | Notes                                                                 |
| ---------------------------- | ------------ | --------------------------------------------------------------------- |
| `HOST`                       | **required** |                                                                       |
| `USERNAME`                   | **required** |                                                                       |
| `PASSWORD`                   | **required** |                                                                       |
| `PORT`                       | `5672`       |                                                                       |
| `VHOST`                      | `/`          |                                                                       |
| `EXCHANGE`                   | `tol`        |                                                                       |
| `DLX`                        | `tol.dlx`    |                                                                       |
| `DECLARE_EXCHANGES`          | `true`       | `false` in staging/prod: exchanges are ops-owned                      |
| `APP_NAME`                   | **required** | to publish or consume; stamped as envelope `source` and AMQP `app_id` |
| `USE_SSL`                    | `false`      |                                                                       |
| `CA_FILE`                    | unset        | CA bundle for an internal CA                                          |
| `WRITE_BATCH_SIZE`           | `100`        |                                                                       |
| `HEARTBEAT`                  | `60`         | seconds                                                               |
| `BLOCKED_CONNECTION_TIMEOUT` | `30`         | seconds                                                               |
| `SOCKET_TIMEOUT`             | `10`         | seconds                                                               |
| `CONNECTION_ATTEMPTS`        | `3`          |                                                                       |
| `RETRY_DELAY`                | `2`          | seconds                                                               |

`RABBITMQ_MANAGEMENT_URL` is read only by the system test
helpers. The SDK itself does not use it.

Email uses the prefix `SMTP_` (change it via `EmailConfig.from_env(prefix=...)`).

| Variable   | Default              | Notes                                                  |
| ---------- | -------------------- | ------------------------------------------------------ |
| `HOST`     | **required**         |                                                        |
| `FROM`     | **required**         | sender address                                         |
| `SECURITY` | `starttls`           | `starttls`, `ssl` or `none`                            |
| `PORT`     | `587` / `465` / `25` | follows `SECURITY`                                     |
| `USERNAME` | unset                | set both or neither; refused when `SECURITY` is `none` |
| `PASSWORD` | unset                |                                                        |
| `TIMEOUT`  | `30`                 | seconds                                                |

`MAILPIT_URL` is read only by the system tests.
