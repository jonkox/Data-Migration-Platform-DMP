from tokenize import group
from elasticsearch import Elasticsearch
import pika
import json

# RabbitMQ
RABBITHOST = "localhost" #os.getenv("RABBITHOST")
RABBITPORT = "30100" #os.getenv("RABBITPORT")
RABBITUSER = "user" #os.getenv("RABBITUSER")
RABBITPASS = "XQnpNkb23Z5RqAly" #os.getenv("RABBITPASS")
RABBITCONSUMEQUEUE = "mysqlconnector" #os.getenv("RABBITQUEUENAME")
RABBITPUBLISHQUEUE = "sqlprocessor" #os.getenv("RABBITQUEUENAME")

# Elastic
ELASTICHOST = "localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICPASS = "5WKt5ymymHVmJsxQ" #os.getenv("ELASTICPASS")

document = {
    "job_id" : "unid",
    "group_id" : "unid1-0"
}

rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
rabbitParameters = pika.ConnectionParameters(
    heartbeat=120,
    blocked_connection_timeout=120,
    host=RABBITHOST,
    port=RABBITPORT,
    credentials=rabbitUserPass
)

cola = pika.BlockingConnection(rabbitParameters).channel()
cola.queue_declare(queue=RABBITCONSUMEQUEUE)

for i in range(0,20000):
    cola.basic_publish(routing_key=RABBITCONSUMEQUEUE, body=json.dumps(document), exchange= '')

def elasticData():
    elasticClient = Elasticsearch("http://"+ELASTICHOST+":"+ELASTICPORT, basic_auth=("elastic",ELASTICPASS))

    if(not (elasticClient.indices.exists(index=["jobs"]))):
        elasticClient.indices.create(index="jobs")

    if(not (elasticClient.indices.exists(index=["groups"]))):
        elasticClient.indices.create(index="groups")

    listOfPersonas = [
        ('9-8569-2630', 'Gerardo Vargas', 1, 'Heredia'),
        ('8-7714-4896', 'Alejandro Mora', 2, 'San Jose'),
        ('3-4540-2769', 'Esteban Rojas', 3, 'Heredia'),
        ('8-7817-9545', 'Andres Jimenez', 4, 'Puntarenas'),
        ('8-3370-2000', 'Mauricio Hernandez', 5, 'Limon'),
        ('8-6225-4060', 'Ronald Castro', 6, 'Heredia'),
        ('2-1935-3873', 'Marvin Gonzalez', 7, 'Guanacaste'),
        ('1-7170-6152', 'Erick Ramirez', 8, 'Limon'),
        ('5-2007-5649', 'Rafael Morales', 9, 'Limon'),
        ('2-6593-7388', 'Juan Carlos Alvarado', 10, 'Heredia')
    ]

    job = {
        "job_id" : "unid1",
        "status": "In-process",
        "msg": "",
        "data_sources": [
            {
                "type": "elasticsearch",
                "name": "destination_es",
                "url": "http://databases-elasticsearch-master-hl.default.svc.cluster.local",
                "port": "9200",
                "usuario": "elastic",
                "password": "Av6gG4ZBIpBYgdeZ"
            },
            {
                "type" : "mysql",
                "name": "people_db",
                "url": "databases-mariadb-primary",
                "port": "3306",
                "usuario": "root",
                "password": "LVOIjwRfuU"
            }
        ],
        "control_data_source": "destination_es",
        "source": {
            "data_source": "people_db",
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
                        "source_data_source": "database_car",
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

    group = {
        "job_id" : "unid1",
        "group_id" : "unid1-0",
        "docs" : []
    }

    for persona in listOfPersonas:
        doc = {}
        doc["cedula"] = persona[0]
        doc["nombre"] = persona[1]
        doc["id"] = persona[2]
        doc["provincia"] = persona[3]
        group["docs"].append(doc)
    
    elasticClient.index(index="jobs", document=job)
    elasticClient.index(index="groups", document=group)

#elasticData()