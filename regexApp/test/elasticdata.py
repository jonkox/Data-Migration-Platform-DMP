from time import sleep
from tokenize import group
from elasticsearch import Elasticsearch
import random
import mariadb
import json
import pika

ELASTICHOST = "localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICPASS = "" #os.getenv("ELASTICPASS")

RABBITHOST = "localhost" #os.getenv("RABBITHOST")
RABBITPORT = "30100" #os.getenv("RABBITPORT")
RABBITUSER = "user" #os.getenv("RABBITUSER")
RABBITPASS = "4VysVe8DAtHWUgit" #os.getenv("RABBITPASS")
RABBITQUEUENAME = "regex_queue" #os.getenv("RABBITQUEUENAME")

docs = []



rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
rabbitParameters = pika.ConnectionParameters(
    host=RABBITHOST,
    port=RABBITPORT,
    credentials=rabbitUserPass
)
try:
    __queue = pika.BlockingConnection(rabbitParameters).channel()
except pika.exceptions.AMQPConnectionError:
    # We can't continue without a queue to publish our results
    raise Exception("Error: Couldn't connect to RabbitMQ")
__queue.queue_declare(queue=RABBITQUEUENAME)

__queue.queue_declare(queue="regex_queue")


elasticClient = Elasticsearch("http://"+ELASTICHOST+":"+ELASTICPORT, basic_auth=("elastic","RYcgQ5MSpmjeRcjj"))
"""
elasticClient.indices.delete(index="jobs")
elasticClient.indices.delete(index="groups")"""

def dataset():
    size = 10
    counter = 1
    group = 0
    #Connect to mariadb
    try:
        conn = mariadb.connect(
            user="root",
            password="iy5PtSwCIo",
            host="127.0.0.1",
            port=32100,
            database="my_database")

        print("Connection succesfully")
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    
    # Get Cursor
    cur = conn.cursor()

    # elasticClient.indices.delete(index="jobs")
    # elasticClient.indices.delete(index="groups")

    if(not (elasticClient.indices.exists(index=["jobs"]))):
        elasticClient.indices.create(index="jobs")
    
    with open("regexApp/test/ejemplo01.json") as archivo:
        datos = json.load(archivo)

    elasticClient.index(index="jobs", document=datos)
    
    if(not (elasticClient.indices.exists(index=["groups"]))):
        elasticClient.indices.create(index="groups")
    
    



    cur.execute("""SELECT p.cedula, p.nombre, p.id, p.provincia, c.description
                    FROM persona AS p
                    INNER JOIN 
                    car AS c
                    ON
                    p.id = c.owner
                    LIMIT 2300""")

    
    for i in cur:
        dato = {
            "cedula" :      i[0],
            "nombre" :      i[1],
            "id" :          i[2],
            "provincia" :   i[3],
            "description" : i[4]
        }

        
        if counter <= size:
            docs.append(dato)
            counter += 1
        
        if counter > size:
            doc = {
                    "job_id" : "nuevojob",
                    "group_id": "",
                    "docs": docs
                    }
            
            doc["group_id"] = "nuevojob-" + str(group)
            elasticClient.index(index="groups", document=doc)
            cant = len(docs)
            docs.clear()
            counter = 1
            group += 1

    jobs = []
    for i in range(2300):
        doc = {
        "job_id" : "nuevojob",
        "group_id": "nuevojob-"+str(i),
        }
        __queue.basic_publish(routing_key=RABBITQUEUENAME, body=json.dumps(doc), exchange='')
        jobs.append(doc)
    
    __queue.close()
            
            #print(f"LA CANTIDAD DE DATOS INSERTADOS FUE DE {cant}")

    #Close connection
    conn.close()

def elastic():

    if(not (elasticClient.indices.exists(index=["jobs"]))):
        elasticClient.indices.create(index="jobs")

    dataset()

    doc = {
        "job_id" : "nuevojob",
        "group_id": "job666-100",
        "docs": docs
        }

    string = "nuevojob"

    for i in range(0,1):
        doc["job_id"] = "nuevojob" + str(random.randint(0,1000))
        elasticClient.index(index="jobs", document=doc)

op = 3

if op == 1:
    with open("regexApp/test/ejemplo2.json") as archivo:
        datos = json.load(archivo)
    
    elasticClient.index(index="jobs", document=datos)


if op == 2:
    jobs = []
    for i in range(2300):
        doc = {
        "job_id" : "nuevojob",
        "group_id": "nuevojob-"+str(i),
        }
        __queue.basic_publish(routing_key=RABBITQUEUENAME, body=json.dumps(doc), exchange='')
        jobs.append(doc)
    
    __queue.close()

if op == 3:
    dataset()
    with open("regexApp/test/ejemplo2.json") as archivo:
        datos = json.load(archivo)
    
    elasticClient.index(index="jobs", document=datos)
