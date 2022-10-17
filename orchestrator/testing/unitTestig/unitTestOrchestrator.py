import pika
import json
from time import sleep
from elasticsearch import Elasticsearch

ELASTICHOST = "localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "elastic"
ELASTICPASS = "vLjjh9ojWfyn4FNq" #os.getenv("ELASTICPASS")

RABBITHOST = "localhost" 
RABBITPORT = "30100" 
RABBITUSER = "user" 
RABBITPASS = "64iBHzjtzmxs2ZPv"
RABBITQUEUENAME = "orchestrator"

global message_number
message_number = 0

def consume(ch, method, properties, msg):
    global message_number
    message = json.loads(msg)
    message = json.dumps(message, indent=6, separators=(',',':'))
    message_number += 1
    print("\nMessage number " + str(message_number))
    print(message)

elasticClient = Elasticsearch("http://"+ELASTICHOST+":"+ELASTICPORT, basic_auth=(ELASTICUSER,ELASTICPASS))

"""if((elasticClient.indices.exists(index=["jobs"]))):
    elasticClient.indices.delete(index="jobs")"""
#elasticClient.indices.create(index="jobs")

job0 = {
    "job_id": "job0",
    "status": "new",
    "msg": "",
    "data_sources": [
        {
            "type": "mysql",
            "name": "mariadb",
            "url": "databases-mariadb-primary",
            "port": "3306",
            "usuario": "root",
            "password": "IteAgY6fBV"
        },
        {
            "type": "elasticsearch",
            "name": "destination_es",
            "url": "http://databases-elasticsearch-master-hl.default.svc.cluster.local",
            "port": "9200",
            "usuario": "elastic",
            "password": "5WKt5ymymHVmJsxQ"
        }
    ],
    "control_data_source": "destination_es",
    "source": {
        "data_source": "mariadb",
        "expression": "SELECT * FROM persona ORDER BY cedula",
        "grp_size": "100"
    },
    "stages" : [
        {
            "name": "extract",
            "source_queue": "extract",
            "destination_queue": "%{transform->transformation->add_car}%"
        },
        {
            "name": "transform",
            "transformation": [
                {
                    "name": "add_car",
                    "type": "sql_transform",
                    "table": "car",
                    "expression": "SELECT %{field_description}% FROM %{table}% WHERE %{field_owner}% = %{doc_field}%",
                    "source_data_source": "mariadb",
                    "destination_data_source": "destination_es",
                    "doc_field": "id",
                    "source_queue": "sql_queue",
                    "destination_queue": "%{transform->transformation->myregex}%",
                    "fields_mapping": {
                        "field_description": "description",
                        "field_owner": "owner"
                    }
                },
                {
                    "name": "myregex",
                    "type": "regex_transform",
                    "regex_config": {
                        "regex_expression": "^.* ([a-zA-z]{3}-[0-9]{3}) .*$",
                        "group": "1",
                        "field": "description"
                    },
                    "field_name": "placa",
                    "source_queue": "regex_queue",
                    "destination_queue": "%{load}%"
                }
            ]
        },
        {
            "name": "load",
            "source_queue": "ready",
            "destination_data_source": "destination_es",
            "index_name": "persona"
        }
    ]
}

job1 = {
    "job_id": "job1",
    "status": "new",
    "msg": "",
    "data_sources": [
        {
            "type": "mysql",
            "name": "mariadb",
            "url": "databases-mariadb-primary",
            "port": "3306",
            "usuario": "root",
            "password": "IteAgY6fBV"
        },
        {
            "type": "elasticsearch",
            "name": "destination_es",
            "url": "http://databases-elasticsearch-master-hl.default.svc.cluster.local",
            "port": "9200",
            "usuario": "elastic",
            "password": "5WKt5ymymHVmJsxQ"
        }
    ],
    "control_data_source": "destination_es",
    "source": {
        "data_source": "mariadb",
        "expression": "SELECT * FROM persona ORDER BY cedula",
        "grp_size": "10"
    },
    "stages" : [
        {
            "name": "extract",
            "source_queue": "extract",
            "destination_queue": "%{transform->transformation->add_car}%"
        },
        {
            "name": "transform",
            "transformation": [
                {
                    "name": "add_car",
                    "type": "sql_transform",
                    "table": "car",
                    "expression": "SELECT %{field_description}% FROM %{table}% WHERE %{field_owner}% = %{doc_field}%",
                    "source_data_source": "mariadb",
                    "destination_data_source": "destination_es",
                    "doc_field": "id",
                    "source_queue": "sql_queue",
                    "destination_queue": "%{transform->transformation->myregex}%",
                    "fields_mapping": {
                        "field_description": "description",
                        "field_owner": "owner"
                    }
                },
                {
                    "name": "myregex",
                    "type": "regex_transform",
                    "regex_config": {
                        "regex_expression": "^.* ([a-zA-z]{3}-[0-9]{3}) .*$",
                        "group": "1",
                        "field": "description"
                    },
                    "field_name": "placa",
                    "source_queue": "regex_queue",
                    "destination_queue": "%{load}%"
                }
            ]
        },
        {
            "name": "load",
            "source_queue": "ready",
            "destination_data_source": "destination_es",
            "index_name": "persona"
        }
    ]
}

job2 = {
    "job_id": "job2",
    "status": "new",
    "msg": "",
    "data_sources": [
        {
            "type": "mysql",
            "name": "mariadb",
            "url": "databases-mariadb-primary",
            "port": "3306",
            "usuario": "root",
            "password": "IteAgY6fBV"
        },
        {
            "type": "elasticsearch",
            "name": "destination_es",
            "url": "http://databases-elasticsearch-master-hl.default.svc.cluster.local",
            "port": "9200",
            "usuario": "elastic",
            "password": "5WKt5ymymHVmJsxQ"
        }
    ],
    "control_data_source": "destination_es",
    "source": {
        "data_source": "mariadb",
        "expression": "SELECT * FROM car ORDER BY id",
        "grp_size": "50"
    },
    "stages" : [
        {
            "name": "extract",
            "source_queue": "extract",
            "destination_queue": "%{transform->transformation->add_car}%"
        },
        {
            "name": "transform",
            "transformation": [
                {
                    "name": "add_car",
                    "type": "sql_transform",
                    "table": "car",
                    "expression": "SELECT %{field_description}% FROM %{table}% WHERE %{field_owner}% = %{doc_field}%",
                    "source_data_source": "mariadb",
                    "destination_data_source": "destination_es",
                    "doc_field": "id",
                    "source_queue": "sql_queue",
                    "destination_queue": "%{transform->transformation->myregex}%",
                    "fields_mapping": {
                        "field_description": "description",
                        "field_owner": "owner"
                    }
                },
                {
                    "name": "myregex",
                    "type": "regex_transform",
                    "regex_config": {
                        "regex_expression": "^.* ([a-zA-z]{3}-[0-9]{3}) .*$",
                        "group": "1",
                        "field": "description"
                    },
                    "field_name": "placa",
                    "source_queue": "regex_queue",
                    "destination_queue": "%{load}%"
                }
            ]
        },
        {
            "name": "load",
            "source_queue": "ready",
            "destination_data_source": "destination_es",
            "index_name": "persona"
        }
    ]
}

rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
rabbitParameters = pika.ConnectionParameters(
    heartbeat=120,
    blocked_connection_timeout=120,
    host=RABBITHOST,
    port=RABBITPORT,
    credentials=rabbitUserPass
)
try:
    queue = pika.BlockingConnection(rabbitParameters).channel()
except pika.exceptions.AMQPConnectionError:
    # We can't continue without a queue to publish our results
    raise Exception("Error: Couldn't connect to RabbitMQ")
queue.queue_declare(queue=RABBITQUEUENAME)
#queue.basic_consume(queue=RABBITQUEUENAME, on_message_callback=consume, auto_ack=True)


jobs = [job1]

for job in jobs:
    elasticClient.index(index="jobs", document=job)

#queue.start_consuming()

