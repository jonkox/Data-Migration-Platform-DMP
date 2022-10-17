from email import message
from    time            import sleep
from    tokenize        import group
from    elasticsearch   import Elasticsearch
import sys
import  random
import  mariadb
import  json
import  pika
#import  DATASET

ELASTICHOST         = "localhost"
ELASTICPORT         = "32500"
ELASTICPASS         = ""

RABBITHOST          = "localhost"
RABBITPORT          = "30100"
RABBITUSER          = "user"
RABBITPASS          = "64iBHzjtzmxs2ZPv"
RABBITQUEUENAME     = "sqlprocessor"

docs                = []


def dataset():
    size        = 3
    counter     = 1
    group       = 0
    cantidad    = 20
    groups      = int(cantidad/size)+1
    documents   = []
    #datosMaria  = DATASET.dataset()

    #----------------------------
    # RABBITMQ Connection
    #----------------------------
    rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
    rabbitParameters = pika.ConnectionParameters(
    host=RABBITHOST,
    port=RABBITPORT,
    credentials=rabbitUserPass)
    try:
        __queue = pika.BlockingConnection(rabbitParameters).channel()
    except pika.exceptions.AMQPConnectionError:
        # We can't continue without a queue to publish our results
        raise Exception("Error: Couldn't connect to RabbitMQ")
    __queue.queue_declare(queue=RABBITQUEUENAME)
    __queue.queue_declare(queue="regexprocessor")


    #----------------------------
    # ElasticSearch Connection
    #----------------------------
    elasticClient = Elasticsearch("http://"+ELASTICHOST+":"+ELASTICPORT, basic_auth=("elastic","vLjjh9ojWfyn4FNq"))


    #----------------------------
    # MariaDB Connection
    #----------------------------
    try:
        conn = mariadb.connect(
            user="root",
            password="VFZs3RpO1X",
            host="127.0.0.1",
            port=32100,
            database="my_database")

        print("Connection succesfully")
    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    
    # Get Cursor
    cur = conn.cursor()


    if(not (elasticClient.indices.exists(index=["jobs"]))):
        elasticClient.indices.create(index="jobs")
    
    with open("regexApp/test/ejemplo01.json") as archivo:
        datos = json.load(archivo)

    elasticClient.index(index="jobs", document=datos)
    
    if(not (elasticClient.indices.exists(index=["groups"]))):
        elasticClient.indices.create(index="groups")
    
    



    cur.execute(f"""SELECT p.cedula, p.nombre, p.id, p.provincia, c.description
                    FROM persona AS p
                    INNER JOIN 
                    car AS c
                    ON
                    p.id = c.owner
                    LIMIT {cantidad}""")

    
    for i in cur:
        dato = {
            "cedula" :      i[0],
            "nombre" :      i[1],
            "id" :          i[2],
            "provincia" :   i[3],
            "description" : i[4]
        }
        documents.append(dato)

    
    for i in range(groups):
        docs = []
        for j in range(size):
            if documents == []:
                break
            docs.append(documents[0])
            documents.pop(0)

        doc = {
                "job_id" : "nuevojob",
                "group_id": "",
                "docs": docs
                }
        
        doc["group_id"] = "nuevojob-" + str(i)
        elasticClient.index(index="groups", document=doc)

        message = {
        "job_id" : doc["job_id"],
        "group_id": "nuevojob-"+str(i),
        }
        __queue.basic_publish(routing_key=RABBITQUEUENAME, body=json.dumps(doc), exchange='')
    
    __queue.close()


    #Close connection
    conn.close()

dataset()