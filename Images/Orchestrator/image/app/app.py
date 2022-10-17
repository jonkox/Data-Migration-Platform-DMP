from http.client import PROCESSING
from math import ceil
from time import sleep,time
from elasticsearch import Elasticsearch
import elastic_transport
from prometheus_client import Gauge,start_http_server
import mariadb
import pika
import json
import os

# Environmental Variables

#------------------- PODS -------------------

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

# MariaDB
MARIADBNAME = os.getenv("MARIADBNAME")
MARIADBHOST = os.getenv("MARIADBHOST")
MARIADBPORT = os.getenv("MARIADBPORT")
MARIADBUSER = os.getenv("MARIADBUSER")
MARIADBPASS = os.getenv("MARIADBPASS")

#------------------ TESTING -----------------
"""
# Elasticsearch
ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "" #os.getenv("ELASTICUSER")
ELASTICPASS = "" #os.getenv("ELASTICPASS")

# RabbitMQ
RABBITHOST = "localhost" #os.getenv("RABBITHOST")
RABBITPORT = "30100" #os.getenv("RABBITPORT")
RABBITUSER = "user" #os.getenv("RABBITUSER")
RABBITPASS = "DUWITCIDkvRQBP7e" #os.getenv("RABBITPASS")
RABBITQUEUENAME = "orchestrator" #os.getenv("RABBITQUEUENAME")

# MariaDB
MARIADBNAME = "my_database" #os.getenv("MARIADBNAME")"""

# Enum for colors
class bcolors:
    PROCESSING  = '\33[96m'     #CYAN
    OK          = '\033[92m'    #GREEN
    WARNING     = '\033[93m'    #YELLOW
    FAIL        = '\033[91m'    #RED
    GRAY        = '\033[90m'    #GRAY
    RESET       = '\033[0m'     #RESET COLOR

# Class containing all the orchestrator process
class Orchestrator:
    __groupCount = 0
    __groupSize = 0
    __elasticClientJobs = None
    __mariaClient = None
    __jobDocument = None
    __jobDocumentId = None
    __rabbitConnection = None
    __queue = None
    __time = 0
    __processGroups = 0
    __totalProcessingTime = None
    __avgProcessingTime = None
    __NumberOfProcessedGroups = None
    
    # First of all we want to connect to the elasticsearch job database
    # to wait for jobs
    def __init__(self):

        self.connectElastic(
            ELASTICUSER,
            ELASTICPASS,
            ELASTICHOST,
            ELASTICPORT
        )

        self.connectMariadb(
            MARIADBUSER,
            MARIADBPASS,
            MARIADBHOST,
            MARIADBPORT
        )

        self.__totalProcessingTime = Gauge(
            'orchestrator_total_processing_time', 
            'Total amount of time elapsed when processing'
        )

        self.__avgProcessingTime = Gauge(
            'orchestrator_avg_processing_time', 
            'Average amount of time elapsed when processing'
        )

        self.__NumberOfProcessedGroups = Gauge(
            'orchestrator_number_processed_groups', 
            'Number of Jobs process by orchestrator'
        )
        
        self.__totalProcessingTime.set(0)
        self.__avgProcessingTime.set(0)
        self.__NumberOfProcessedGroups.set(0)

    # Method to start RabbitMQ Queue
    def initQueue(self):
        rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
        rabbitParameters = pika.ConnectionParameters(
            heartbeat=180,
            blocked_connection_timeout=180,
            host=RABBITHOST,
            port=RABBITPORT,
            credentials=rabbitUserPass,
        )
        try:
            self.__rabbitConnection = pika.BlockingConnection(rabbitParameters)
            self.__queue = self.__rabbitConnection.channel()
        except pika.exceptions.AMQPConnectionError:
            # We can't continue without a queue to publish our results
            raise Exception("Error: Couldn't connect to RabbitMQ")
        self.__queue.queue_declare(queue=RABBITQUEUENAME)

    # Simple method used to connect to an elasticsearch database
    def connectElastic(self,user,password,host,port):
        self.__elasticClientJobs = Elasticsearch(
            host+":"+port,
            basic_auth=(user,password)
        )
        try:
            self.__elasticClientJobs.info()
            return True
        except elastic_transport.ConnectionError:
            # We raise an exception because the process 
            # can't continue without a place to look for jobs
            raise Exception("Error: Couldn't connect to Jobs database")
        
    # Simple method used to connect to a MariaDB database
    def connectMariadb(self,user,password,host,port):
        try:
            self.__mariaClient = mariadb.connect(
                user=user,
                password=password,
                host=host,
                port=int(port),
                database=MARIADBNAME
            )
        except mariadb.OperationalError:
            # We raise an exception because the process 
            # can't continue without a place to look get
            # information to publish in elastic
            raise Exception("Error: Couldn't connect to MariaDB database")

    # Method for the starting process
    def startProcess(self):
        # we want to make sure we have a place to look for jobs and to store groups
        if(not (self.__elasticClientJobs.indices.exists(index=["jobs"]))):
            self.__elasticClientJobs.indices.create(index="jobs")
        if(not (self.__elasticClientJobs.indices.exists(index=["groups"]))):
            self.__elasticClientJobs.indices.create(index="groups")
        
        # We need a queue, so we start it here
        self.initQueue()

        # start metrics server
        start_http_server(6942)

        # Making sure pod stays up by providing a infinite loop
        while True:
            sleep(1) # To avoid to filling up elasticsearch with requests, we wait some time

            # Keep pika connection alive by keeping heartbeats alive
            self.__rabbitConnection.process_data_events()

            # Searching process for a new job
            search = self.__elasticClientJobs.search(index="jobs",size="1",query={"match" : {"status":"new"}})
            if(search["hits"]["hits"]):
                print(
                    bcolors.OK + "Job found on elastic: " + bcolors.RESET + "Starting Process " + bcolors.RESET
                )
                startingTime = time()
                self.__jobDocumentId = search["hits"]["hits"][0]["_id"]
                self.__jobDocument = self.__elasticClientJobs.get(index="jobs",id=self.__jobDocumentId)["_source"]
                print(
                    bcolors.PROCESSING + "Processing: " + bcolors.RESET + "Job receive -> " + 
                    bcolors.GRAY + self.__jobDocument["job_id"] + bcolors.RESET
                )
                self.__jobDocument["status"] = "In-process"
                self.__elasticClientJobs.index(index="jobs",id=self.__jobDocumentId,document=self.__jobDocument)
                print(
                    bcolors.PROCESSING + "Processing: " + bcolors.RESET + "Job Status updated -> " + 
                    bcolors.GRAY + "In-process" + bcolors.RESET
                )
                if(self.getGroupCount() == True):
                    continue # we want to skip the next step some thing fails before it
                
                print(
                    bcolors.PROCESSING + "Processing: " + bcolors.RESET + "Group count Obtain -> " + 
                    bcolors.GRAY + str(self.__groupCount) + bcolors.RESET
                )

                self.createDocs()
                # Prometheus metrics
                self.__time += (time() - startingTime)
                self.__totalProcessingTime.set(self.__time)
                self.__avgProcessingTime.set(self.__time/self.__processGroups)

                print(bcolors.OK + "Finished job:" + bcolors.RESET + " -> " + 
                      bcolors.GRAY + self.__jobDocument["job_id"] + bcolors.RESET
                    )

    # before creating any group document, we need to know 
    # the amount of groups/documents we want to create
    # this is the first step in the orchestrator
    def getGroupCount(self):
        try:
            self.__groupSize = int(self.__jobDocument["source"]["grp_size"])
        except TypeError:
            print(
                bcolors.FAIL + "Error:" + bcolors.RESET + " root.source.gpr_size must be a number, document -> " \
                + bcolors.WARNING + self.__jobDocument["job_id"] + bcolors.RESET
                )
            self.failedFile()
            return True

        cursor = self.__mariaClient.cursor()

        countingQuery ="SELECT Count(1) FROM (" + self.__jobDocument["source"]["expression"] + ") subquery"

        try:
            cursor.execute(countingQuery)
        except mariadb.ProgrammingError:
            print(
                bcolors.FAIL + "Error:" + bcolors.RESET + " root.source.expression is not working as it should, document -> " \
                + bcolors.WARNING + self.__jobDocument["job_id"] + bcolors.RESET
            )
            self.failedFile()
            return True

        self.__groupCount = ceil(cursor.fetchone()[0]/self.__groupSize)

        cursor.close()

    # Next step is to create the JSON documents with job_id and 
    # group_id with different offsets, this method is in charge of that.
    def createDocs(self):
        for offset in range(0,self.__groupCount):
            groupDocument = {
                "job_id" : self.__jobDocument["job_id"],
                "group_id" : self.__jobDocument["job_id"] + "-" + str(self.__groupSize*offset) 
            }
            self.__elasticClientJobs.index(index="groups",document=groupDocument)
            self.produce(groupDocument)
            self.__processGroups += 1
            self.__NumberOfProcessedGroups.set(self.__processGroups)
            print(
                    bcolors.PROCESSING + "Processing: " + bcolors.RESET + "Group created and published -> " + 
                    bcolors.GRAY + str(groupDocument) + bcolors.RESET
                )

    #Publish to the queue the new message
    def produce(self, message):
        try:
            self.__queue.basic_publish(routing_key=RABBITQUEUENAME, body=json.dumps(message), exchange='')
        except pika.exceptions.StreamLostError:
            print(f"{bcolors.FAIL} Error: {bcolors.RESET} connection lost, reconnecting... ")
            self.initQueue()
            self.produce(message)

    # This method is very simple, if we managed to get an error without the pod failing
    # we "mark" that job with a "Failed" status, so it is easier to identify bad jobs
    def failedFile(self):
        self.__jobDocument["status"] = "Failed"
        self.__elasticClientJobs.index(index="jobs",id=self.__jobDocumentId,document=self.__jobDocument)

# program initiation
orquestador = Orchestrator()
orquestador.startProcess()
