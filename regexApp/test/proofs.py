import re
from unittest import result
import mariadb
from elasticsearch import Elasticsearch
import json
from datetime import datetime
import os
import pika


#---------------------------------------------------------------------------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
#---------------------------------------------------------------------------------------------------------------------------------------------

#ELASTICSEACH
ELASTICHOST = "localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICPASS = "" #os.getenv("ELASTICPASS")

#RABBITMQ
RABBITHOST = "localhost" #os.getenv("RABBITHOST")
RABBITPORT = "30100" #os.getenv("RABBITPORT")
RABBITUSER = "user" #os.getenv("RABBITUSER")
RABBITPASS = "4VysVe8DAtHWUgit" #os.getenv("RABBITPASS")
RABBITQUEUENAME = "regex_queue" #os.getenv("RABBITQUEUENAME")

#---------------------------------------------------------------------------------------------------------------------------------------------
# GLOBAL VARIABLES
#---------------------------------------------------------------------------------------------------------------------------------------------


docs = []
expression = ""
field = ""
newField = ""



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

def callback(ch, method, properties, body):
    json_object = json.loads(body)
    print(" [x] Received %r" % body)







elasticClient = Elasticsearch("http://"+ELASTICHOST+":"+ELASTICPORT, basic_auth=("elastic","RYcgQ5MSpmjeRcjj"))
print("http://"+ELASTICHOST+":"+ELASTICPORT)
resul = elasticClient.search(index="jobs",size="1",query={"match" : {"_index":"jobs"}})


resul = resul["hits"]["hits"][0]["_source"]



for i in resul["stages"]:
    if i["name"] == "transform":
        for j in i["transformation"]:
            #print(j)
            if j["type"] == "regex_transform":
                
                field = j["regex_config"]["field"]
                newField = j["field_name"]
                expression = j["regex_config"]["regex_expression"]
                #print([expression,field,newField])


_resul = elasticClient.search(index="groups",size="100",query={"match" : {"_index":"groups"}})

_resul = _resul["hits"]["hits"][0]["_source"]



op = 2


if op == 1:
    jobs = []
    for i in range(10):
        doc = {
        "job_id" : "nuevojob",
        "group_id": "nuevojob-"+str(i),
        }
        __queue.basic_publish(routing_key=RABBITQUEUENAME, body=json.dumps(doc), exchange='')
        jobs.append(doc)
    
    __queue.close()
    


if op == 2:
    resp = elasticClient.search(query={"bool": {"must": [{"match": {"_index": "groups"}},{"match": {"group_id": "nuevojob-8"}},{"match": {"job_id": "nuevojob"}}]}})
    print(resp)

    



if op == 3:

    jobs = []
    for i in range(10):
        doc = {
        "job_id" : "nuevojob",
        "group_id": "nuevojob-"+str(i),
        }
        jobs.append(doc)
    print(jobs)
    for i in jobs:
        resul = elasticClient.search(index="jobs",size="1",query={"match" : {"group_id":i["group_id"]}})
        resul = resul["hits"]["hits"][0]["_id"]
        print(resul)

