<!--
SPDX-FileCopyrightText: 2022 Genome Research Ltd.

SPDX-License-Identifier: MIT
-->

# ToL SDK

A Python SDK for ToL services. This is very much a work in progress and is not ready for anyone outside ToL Platforms to use it yet.

## Sciops Integration SDK

### Environment Variables

The SciOps package requires a number of environment variables to be set:

Environment Variable | Description | Default
:---: | :---: | :---:
REDPANDA_URL | URL of the RedPanda message schema server | "127.0.0.1"
REDPANDA_API_KEY | API key needed to access the RedPanda instance | "test"
RABBITMQ_HOST | The address of the Rabbit MQ host | "127.0.0.1"
RABBITMQ_PORT | The Rabbit MQ port number | "5671"
RABBITMQ_USERNAME | The Rabbit MQ user name to use | "psd"
RABBITMQ_PASSWORD | The Rabbit MQ password to use | "psd"
RABBITMQ_VHOST | The Rabbit MQ virtual host | "tol"
RABBITMQ_EXCHANGE | The Rabbit MQ TOL exchange name | "tol-team.tol"
RABBITMQ_ROUTING_KEY | The Rabbit MQ routing key | "crud.1"
RABBITMQ_USE_SSL | Use SSL for the connection | False
RABBITMQ_PUBLISH_RETRY_DELAY | The delay in seconds, between retries when attempting to send a message | 5
RABBITMQ_PUBLISH_RETRIES | Number of retries to use when attempting to send a message | 36
CREATE_LABWARE_MESSAGE_SCHEMA_VERSION | Create Labware message schema version to use | "latest"
UPDATE_LABWARE_MESSAGE_SCHEMA_VERSION | Update Labware message schema version to use | "latest"
REQUESTS_CA_BUNDLE | Certificates path for use with SSL | None

### SSL and Certificates

SSL should be enabled through the `RABBITMQ_USE_SSL` environment variable. 

The certificate path is specified by using the following environment variable:
```
REQUESTS_CA_BUNDLE="/etc/ssl/certs/ca-certificates.crt"
```

Sanger certificates should be available from `/etc/ssl/certs/ca-certificates.crt`, so if running
inside a container they will need to be mounted using, for example [in Docker Compose]:

```
volumes:
      - "./ca-certificates.crt:/etc/ssl/certs/ca-certificates.crt"
```

### Sending Messages

The following example shows the basic idea:

```
sample_uuid = str(uuid.uuid4())
study_uuid = str(uuid.uuid4())
labware_uuid = str(uuid.uuid4())

# Build Create Labware message
create_msg = CreateLabwareMessage(
    message_uuid=str(uuid.uuid4()),
    message_create_date_utc=datetime.datetime.now(datetime.timezone.utc),
    labware_type="Plate12x8",
    labware_uuid=labware_uuid,
    barcode="1",
    samples=[
        Sample(
            sample_uuid=sample_uuid,
            study_uuid=study_uuid,
            sanger_sample_id="TestSample1",
            location="A1",
            supplier_sample_name="TestSample1SupplierName",
            volume="5",
            concentration="5",
            public_name="TestSample1PublicName",
            taxon_id="10090",
            common_name="Mus Musculus",
            donor_id="TestSample1",
            library_type="Library1",
            country_of_origin="United Kingdom",
            sample_collection_date_utc=datetime.datetime.now(datetime.timezone.utc)
        )
    ]
)

# Build an Update Labware message
update_msg = UpdateLabwareMessage(
    message_uuid=str(uuid.uuid4()),
    message_create_date_utc=datetime.datetime.now(datetime.timezone.utc),
    labware_updates=[
        Update(
            uuid=labware_uuid,
            name="barcode",
            value="2"
        )
    ],
    sample_updates=[
        Update(
            uuid=sample_uuid,
            name="volume",
            value="6"
        )
    ]
)

# Send
publisher = SciOpsPublisher()
publisher.send_message(create_msg)
publisher.send_message(update_msg)
```

### Receiving Feedback
A feedback message will be received for each sent message and will show if any errors were encountered. 

Feedback messages can be asynchronously received using the following code:

```
consumer = SciOpsConsumer(FeedbackProcessor())
consumer.start()
```

A specific _FeedbackProcessor_ implementation should be created. The one used above will
just print out any feedback messages received - see `response_processors.py`. Override its `process_message` method
and implement it as follows:

```
def process_message(self, headers, body):
    ret = super().process_message(headers, body)
    <do some custom processing here, save to database etc>
    return ret

```
### Available Traction Library Types
The following is a list of Production/UAT Traction *library type*s that may be specified in a message:

* Pacbio_Amplicon
* Pacbio_HiFi
* Pacbio_HiFi_mplx
* Pacbio_IsoSeq
* PacBio_IsoSeq_mplx
* Pacbio_Microbial_mplx
* PacBio_Ultra_Low_Input
* PacBio_Ultra_Low_Input_mplx
* Saphyr_v1

### Checking successful message delivery in SciOps Traction GUI:
The GUI URL is: [https://uat.traction.psd.sanger.ac.uk/#/pacbio/samples](https://uat.traction.psd.sanger.ac.uk/#/pacbio/samples)

