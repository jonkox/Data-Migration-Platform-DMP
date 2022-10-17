from elasticsearch import Elasticsearch
import elastic_transport
import pika
import os
import json

# Elasticsearch
ELASTICHOST = os.getenv("ELASTICHOST")
ELASTICPORT = os.getenv("ELASTICPORT")
ELASTICUSER = os.getenv("ELASTICUSER")
ELASTICPASS = os.getenv("ELASTICPASS")

# RabbitMQ
RABBITHOST = os.getenv("RABBITHOST")
RABBITPORT = os.getenv("RABBITPORT")
RABBITUSER = os.getenv("RABBITUSER")
RABBITPASS = os.getenv("RABBITPASS")
RABBITQUEUENAME = os.getenv("RABBITQUEUENAME") #send message


# Class for printing colors
class bcolors:
    OK      = '\033[92m'    #GREEN
    RESET   = '\033[0m'     #RESET COLOR

#main class
class Produce:
    ElasticClient = None

    def __init__(self):
        self.connectDbElastic(ELASTICHOST,ELASTICPORT,ELASTICUSER,ELASTICPASS)
        self.startProduce(RABBITUSER,RABBITPASS,RABBITHOST,RABBITPORT,RABBITQUEUENAME)

    def connectDbElastic(self,pHost,pPort,pUser,pPass):
        try:
            self.ElasticClient = Elasticsearch(
                    pHost+":"+pPort,
                    basic_auth=(pUser,pPass)
                )
        except elastic_transport.ConnectionError:
            raise Exception ("Error: Couldn't connect to database Elastic")

    def startProduce(self,pUser,pPass,pHost,pPort,pQueue):
        credentials2 = pika.PlainCredentials(pUser, pPass)
        parameters2 = pika.ConnectionParameters(host=pHost, port=pPort, credentials=credentials2) 
        connection2 = pika.BlockingConnection(parameters2)
        channel2 = connection2.channel()
        channel2.queue_declare(queue=pQueue)

        #Publicamos en elastic un documento en el indice groups que sea "job_id":"json123","group_id":"json123-0"
        msg = "{\"job_id\": \"json123\",\"group_id\":\"json123-0\"}"
        contenido = {'job_id':"json123",'group_id':"json123-0"}
        self.ElasticClient.index(index="groups",id=1,document=contenido)
        channel2.basic_publish(exchange='', routing_key=RABBITQUEUENAME, body=msg) 
        print(f"{bcolors.OK} Mensaje que envia produce --->: {bcolors.RESET}",msg)
        connection2.close() #Solo envia ese mensaje
Produce()       
