from time import sleep
from elasticsearch import Elasticsearch
import os
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

global message_number

def consume(ch, method, properties, msg):
    global message_number
    message = json.loads(msg)
    message = json.dumps(message, indent=6, separators=(',',':'))
    message_number += 1
    print("\nMessage number " + str(message_number))
    print(message)

def elasticData():
    elasticClient = Elasticsearch("http://"+ELASTICHOST+":"+ELASTICPORT, basic_auth=("elastic",ELASTICPASS))
    if((elasticClient.indices.exists(index=["jobs"]))):
        elasticClient.indices.delete(index="jobs")
    if((elasticClient.indices.exists(index=["groups"]))):
        elasticClient.indices.delete(index="groups")

    
    elasticClient.indices.create(index="jobs")
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

    with open(os.path.join(os.path.dirname(__file__),"ejemplo01.json")) as archivo:
        job = json.load(archivo)
    
    group = {
        "job_id" : "job0",
        "group_id" : "job0-0",
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

message_number = 0

document = {
    "job_id" : "job0",
    "group_id" : "job0-0"
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
cola2 = pika.BlockingConnection(rabbitParameters).channel()
cola.queue_declare(queue=RABBITCONSUMEQUEUE)
cola2.queue_declare(queue=RABBITPUBLISHQUEUE)
cola2.basic_consume(queue=RABBITPUBLISHQUEUE, on_message_callback=consume, auto_ack=True)

elasticData()
sleep(3)
cola.basic_publish(routing_key=RABBITCONSUMEQUEUE, body=json.dumps(document), exchange= '')
cola2.start_consuming()


