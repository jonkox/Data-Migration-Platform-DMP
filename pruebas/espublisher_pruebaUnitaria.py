"""
Unit test for Elasticsearch Publisher APP
"""

import pika
import elasticsearch
import os, sys
from time import sleep

from elasticsearch import Elasticsearch

sys.path.append(os.path.join(
        os.path.dirname(__file__), 
        '..', 
        'elasticsearch_publisher_app',
        'image',
        'app'
    )
)
from elasticsearchPublisher import ElasticsearchPublisher

# Class for printing colors
class bcolors:
    OK      = '\033[92m'    #GREEN
    WARNING = '\033[93m'    #YELLOW
    FAIL    = '\033[91m'    #RED
    RESET   = '\033[0m'     #RESET COLOR
    
ELASTICHOST = "http://localhost"
ELASTICPORT = "32500"
ELASTICUSER = "elastic" 
ELASTICPASS = "m2Hl6qYVLMNFDfdZ" 

# Create a client
ESConnection = Elasticsearch(
    ELASTICHOST+":"+ELASTICPORT,
    basic_auth=(ELASTICUSER,ELASTICPASS)
)

# Check if connection was successful
try:
    ESConnection.info()
except:
    raise Exception("Error: Couldn't connect to Elasticsearch")


def kibanaPublishingSimulation():
    # Open testing files and publish them in ES index
    localFile = os.path.join(os.path.dirname(__file__), 'ejemplo01.json')
    f = open(localFile,  "r")
    dataFromFile = f.read()

    response = ESConnection.index(
            index = "jobs",
            id = "job606",
            body = dataFromFile,
        )

    localFile = os.path.join(os.path.dirname(__file__), 'documentoGrupo.json')
    f = open(localFile,  "r")
    dataFromFile = f.read()

    response = ESConnection.index(
            index = "groups",
            id = "job606-100",
            body = dataFromFile,
        )

    print(f"{bcolors.OK} Documents were successfully published to ES indices for testing {bcolors.RESET}")


def createQueue():
    # Create connection
    rabbitUserPass = pika.PlainCredentials("user","iX4rMustwltDPp7Y")
    rabbitConnectionParameters = pika.ConnectionParameters(
            host='localhost', 
            port='30100',
            credentials=rabbitUserPass
    )
    connection = pika.BlockingConnection(rabbitConnectionParameters)
    channel = connection.channel()

    QUEUE_NAME = 'ready' 

    channel.queue_declare(queue = QUEUE_NAME)

    print(f"{bcolors.OK} Created Queue for testing {bcolors.RESET}")

    connection.close()


def regexFinishedProcess():
    rabbitUserPass = pika.PlainCredentials("user","iX4rMustwltDPp7Y")
    rabbitConnectionParameters = pika.ConnectionParameters(
            host='localhost', 
            port='30100',
            credentials=rabbitUserPass
        )
    connection = pika.BlockingConnection(rabbitConnectionParameters)
    channel = connection.channel()

    QUEUE_NAME = 'ready' 

    # Open file for testing
    localFile = os.path.join(os.path.dirname(__file__), 'msg.json')
    f = open(localFile,  "r")
    dataFromFile = f.read()

    # Simulation: Send message from "REGEX-PROCESSOR" to ES PUBLISHER APP
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=dataFromFile)

    print(f"{bcolors.OK} Simulation: REGEX-PROCESSOR finished and sent message to publisher {bcolors.RESET}")

    connection.close()


def process(ch, method):
    ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
    print(f"{bcolors.OK} Process finished {bcolors.RESET}")


def callback(ch, method, properties, body):
    print(f"{bcolors.OK} MSG received from REGEX-PROCESSOR = {bcolors.RESET}", body)
    process(ch, method)


def createESpublisher():
    esPublisher = ElasticsearchPublisher()


# -------------------- UNIT TEST PROCESS -------------------
# 1. Simulate when an user publishes a document in "jobs" index using Kibana
kibanaPublishingSimulation()

# 2. Simulate that the queue needed already exists 
createQueue()

# 3. Simulate that REGEX-PROCESSOR APP finished its job and sent message to the queue
regexFinishedProcess()

# 4. Initialize the Elasticsearch publisher app to start the process
createESpublisher()