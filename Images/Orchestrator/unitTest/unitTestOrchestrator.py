import pika
import json
import os
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

if((elasticClient.indices.exists(index=["jobs"]))):
    elasticClient.indices.create(index="jobs")

with open(os.path.join(os.path.dirname(__file__),"job0.json")) as archivo:
    job0 = json.load(archivo)

with open(os.path.join(os.path.dirname(__file__),"job1.json")) as archivo:
    job1 = json.load(archivo)

with open(os.path.join(os.path.dirname(__file__),"job2.json")) as archivo:
    job2 = json.load(archivo)

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

# For retrieving messages from the publishing queue
#queue.basic_consume(queue=RABBITQUEUENAME, on_message_callback=consume, auto_ack=True)

jobs = [job0,job1,job2]

for job in jobs:
    elasticClient.index(index="jobs", document=job)

# For retrieving messages from the publishing queue
#queue.start_consuming()

