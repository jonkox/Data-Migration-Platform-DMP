import sys
from math import ceil
from time import sleep,time
from elasticsearch import Elasticsearch
import elastic_transport
import mariadb
import pika
import json
import os


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
RABBITQUEUENAME = os.getenv("RABBITQUEUENAME") #see
RABBITQUEUEMYSQL = os.getenv("RABBITQUEUEMySQL") #send message

# MariaDB
MARIADBNAME = os.getenv("MARIADBNAME")
MARIADBHOST = os.getenv("MARIADBHOST")
MARIADBPORT = os.getenv("MARIADBPORT")
MARIADBUSER = os.getenv("MARIADBUSER")
MARIADBPASS = os.getenv("MARIADBPASS")

# Class for printing colors
class bcolors:
    OK      = '\033[92m'    #GREEN
    WARNING = '\033[93m'    #YELLOW
    FAIL    = '\033[91m'    #RED
    RESET   = '\033[0m'     #RESET COLOR

class MySQLConnector:
    ElasticClient = None
    MariaClient = None

    def __init__(self):
        self.connectDbElastic(ELASTICHOST,ELASTICPORT,ELASTICUSER,ELASTICPASS)
        self.startConsume(RABBITUSER,RABBITPASS,RABBITHOST,RABBITPORT,RABBITQUEUENAME)


    def connectDbElastic(self,pHost,pPort,pUser,pPass):
        try:
            self.ElasticClient = Elasticsearch(
                    pHost+":"+pPort,
                    basic_auth=(pUser,pPass)
                )
        except elastic_transport.ConnectionError:
            raise Exception ("Error: Couldn't connect to database Elastic")
    
    def connectDbMaria(self,pHost,pPort,pUser,pPass,pName):
        try:
            self.MariaClient = mariadb.connect(
                    host=pHost, 
                    port= int(pPort),
                    user=pUser, 
                    password= pPass, 
                    database= pName)
        except:
            print("Error: Couldn't connect to database Maria") 

    def startConsume(self,pUser,pPass,pHost,pPort,pQueue):
        credentials_ = pika.PlainCredentials(pUser, pPass)
        parameters = pika.ConnectionParameters(host=pHost, port=pPort, credentials=credentials_)
        connection = pika.BlockingConnection(parameters)
        channelConsuming = connection.channel()
        channelConsuming.queue_declare(queue=pQueue)
        channelConsuming.basic_consume(queue=pQueue, on_message_callback= self.callback, auto_ack=False)

        channelConsuming.start_consuming()

    def startProduce(self,pUser,pPass,pHost,pPort,pQueue,pMsg):
        print(f"{bcolors.OK} MySQL Connector: {bcolors.RESET} Send message")
        credentials2 = pika.PlainCredentials(pUser, pPass)
        parameters2 = pika.ConnectionParameters(host=pHost, port=pPort, credentials=credentials2) 
        connection2 = pika.BlockingConnection(parameters2)
        channel2 = connection2.channel()
        channel2.queue_declare(queue=pQueue)
        msg2 =pMsg
        channel2.basic_publish(exchange='', routing_key=RABBITQUEUEMYSQL, body=msg2) 
        connection2.close()

MySQLConnector()       
