import json
import pika
import elasticsearch
import os

from elasticsearch import Elasticsearch
from prometheus_client import Gauge, start_http_server
from time import sleep,time

# ------------ ENVIRONMENT  VARIABLES FOR CONNECTIONS -------

""""
# Used for testing without environment variables

ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "elastic" #os.getenv("ELASTICUSER")
ELASTICPASS = "m2Hl6qYVLMNFDfdZ" #cambiar contraseña si se desinstala #os.getenv("ELASTICPASS")

RABBITHOST = 'localhost'
RABBITPORT = '30100'
RABBITUSER = 'user'
RABBITPASS = 'iX4rMustwltDPp7Y'
RABBITQUEUENAME = 'espublisher'
"""

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
RABBITQUEUENAME = os.getenv("RABBITQUEUENAME")


# Class for printing colors
class bcolors:
    OK      = '\033[92m'    #GREEN
    WARNING = '\033[93m'    #YELLOW
    FAIL    = '\033[91m'    #RED
    RESET   = '\033[0m'     #RESET COLOR


class ElasticsearchPublisher:
    # Variables for metrics
    time = 0
    processedGroups = 0
    totalProcessingTime = None
    avgProcessingTime = None
    numberOfProcessedGroups = None

    ESConnection = None

    #Constructor method
    def __init__(self):
        # Initialize variables for metrics
        self.totalProcessingTime = Gauge(
            'espublisher_total_processing_time', 
            'Total amount of time elapsed when processing')
        
        self.avgProcessingTime = Gauge(
            'espublisher_avg_processing_time', 
            'Average amount of time elapsed when processing')

        self.numberOfProcessedGroups = Gauge(
            'espublisher_number_processed_groups', 
            'Number of Jobs process by elasticsearch publisher')
        
        self.totalProcessingTime.set(0)
        self.avgProcessingTime.set(0)
        self.numberOfProcessedGroups.set(0)

        # #Starting server where we send metrics
        start_http_server(6944)

        self.connectElastic(ELASTICUSER,ELASTICPASS,ELASTICHOST,ELASTICPORT)
        self.connectRabbitmq(RABBITUSER, RABBITPASS, RABBITHOST, RABBITPORT, RABBITQUEUENAME)
        
    
    def connectElastic(self,user,password,host,port):
        # Create elasticsearch client
        self.ESConnection = Elasticsearch(
            host+":"+port,
            basic_auth=(user,password)
        )

         # Check if ES connection was succesfull 
        try:
            self.ESConnection.info()
        except:
            raise Exception("Error: Couldn't connect to Elasticsearch")
    

    def getConfigDoc(self, ESConnection, job_id):
        searchResult = self.ESConnection.search(index="jobs",size="1",query={"match" : {"job_id" : job_id}})
        configDoc = None
        if(searchResult["hits"]["hits"]):
            configDocID = searchResult["hits"]["hits"][0]["_id"]
            configDoc = self.ESConnection.get(index="jobs", id=configDocID)["_source"]
        
        return configDoc


    def searchJob(self, jobId):
        searchResult = self.ESConnection.search(index="jobs",size=1,query={"match" : {"job_id" : jobId}})
        print(f"{bcolors.OK} ES Publisher: {bcolors.RESET} Search in 'jobs' index was successful")
        return searchResult["hits"]["hits"][0]["_source"]


    def searchGroup(self, groupId):
        searchResult = self.ESConnection.search(index="groups",size=1,query={"match" : {"group_id" : groupId}})
        print(f"{bcolors.OK} ES Publisher: {bcolors.RESET} Search in 'groups' index was successful")
        return searchResult["hits"]["hits"][0]["_source"]


    def workForPod(self, jsonObject):
        print(f"{bcolors.OK} ES Publisher: {bcolors.RESET} Process started")

        # Start timer for metrics
        startingTime = time()

        # Get group_id from the document that was received
        group_id = jsonObject["group_id"]

        # Get job_id from the document that was received
        job_id = jsonObject["job_id"]

        try:
            # Search in 'groups' index and get document identified by group_id
            groupDoc_body = self.searchGroup(group_id)

            # Search in 'jobs' index and get document identified by job_id
            jobDoc_body = self.searchJob(job_id)

        except IndexError or KeyError:
            return False  # Process wasn't successful 

        # Store documents for publishing
        docs = groupDoc_body["docs"]

        # ------------ PUBLISH DOCUMENT -------------
        # Search configuration doc to get publishing index name
        configDoc = self.getConfigDoc(self.ESConnection, job_id)

        # Name of index where the documents will be published
        publishingIndex = configDoc["stages"][2]["index_name"] 

        for doc in docs:
            publishingResult = self.ESConnection.index(
                index = publishingIndex,
                document = doc,
            )
        
        print(f"{bcolors.OK} ES Publisher: {bcolors.RESET} Documents were successfully published")
        
        # ----------- DELETE DOCUMENT FROM INDEX 'GROUPS' ---------------
        deleteDocResult = self.ESConnection.delete(index="groups", id= group_id)

        print(f"{bcolors.OK} ES Publisher: {bcolors.RESET} Document was successfully deleted from index")

        # ---------- Prometheus metrics --------------
        self.time += (time() - startingTime)
        self.processedGroups = self.processedGroups + 1
        self.numberOfProcessedGroups.set(self.processedGroups)
        self.totalProcessingTime.set(self.time)
        self.avgProcessingTime.set(self.time/self.processedGroups)

        return True     # Process was successfully finished

    def callback(self, ch, method, properties, body):
    
        json_object = json.loads(body)

        if self.workForPod(json_object):
            # This notifies that the message was received succesfully
            ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
            print(f"{bcolors.OK} ES Publisher: {bcolors.RESET} Process finished")
        else:
            print(f"{bcolors.FAIL} ES Publisher: {bcolors.RESET} Error in process, waiting for next message")
    

    def connectRabbitmq(self, user, password, host, port, queueName):
        # Connect to rabbtimq
        rabbitUserPass = pika.PlainCredentials(user, password)

        rabbitConnectionParameters = pika.ConnectionParameters(
            host= host, 
            port= port,
            credentials= rabbitUserPass
        )

        try:
            connection = pika.BlockingConnection(rabbitConnectionParameters)
            channel = connection.channel()
            channel.queue_declare(queue = RABBITQUEUENAME)
            channel.basic_qos(prefetch_count=1)
        except pika.exceptions.AMQPConnectionError:
            raise Exception("Error: Couldn't connect to RabbitMQ")

        channel.basic_consume(queue= RABBITQUEUENAME, auto_ack=False, on_message_callback=self.callback)
        channel.start_consuming()


ElasticsearchPublisher()