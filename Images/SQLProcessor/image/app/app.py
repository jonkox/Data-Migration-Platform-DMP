from operator import truediv
from prometheus_client import Gauge,start_http_server
from elasticsearch import Elasticsearch
import elastic_transport
from time import time,sleep
import re as Regex
import mariadb
import json
import pika
import os

# RabbitMQ
RABBITHOST = os.getenv("RABBITHOST")
RABBITPORT = os.getenv("RABBITPORT")
RABBITUSER = os.getenv("RABBITUSER")
RABBITPASS = os.getenv("RABBITPASS")
RABBITCONSUMEQUEUE = os.getenv("RABBITCONSUMEQUEUE")
RABBITPUBLISHQUEUE = os.getenv("RABBITPUBLISHQUEUE")

# Elastic
ELASTICHOST = os.getenv("ELASTICHOST")
ELASTICPORT = os.getenv("ELASTICPORT")
ELASTICUSER = os.getenv("ELASTICUSER")
ELASTICPASS = os.getenv("ELASTICPASS")

# MariaDB
MARIADBNAME = os.getenv("MARIADBNAME")
MARIADBHOST = os.getenv("MARIADBHOST")
MARIADBPORT = os.getenv("MARIADBPORT")
MARIADBUSER = os.getenv("MARIADBUSER")
MARIADBPASS = os.getenv("MARIADBPASS")

#SQLProcessor
SQLPROCESSORRETRIES = os.getenv("SQLPROCESSORRETRIES")
SQLPROCESSORTIMEOUT= os.getenv("SQLPROCESSORTIMEOUT")

"""
# RabbitMQ
RABBITHOST = "localhost" #os.getenv("RABBITHOST")
RABBITPORT = "30100" #os.getenv("RABBITPORT")
RABBITUSER = "user" #os.getenv("RABBITUSER")
RABBITPASS = "XQnpNkb23Z5RqAly" #os.getenv("RABBITPASS")
RABBITCONSUMEQUEUE = "mysqlprocessor" #os.getenv("RABBITQUEUENAME")
RABBITPUBLISHQUEUE = "sqlprocessor" #os.getenv("RABBITQUEUENAME")

# Elastic
ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "elastic" #os.getenv("ELASTICUSER")
ELASTICPASS = "5WKt5ymymHVmJsxQ" #os.getenv("ELASTICPASS")

# MariaDB
MARIADBNAME = "my_database" #os.getenv("MARIADBNAME")
MARIADBHOST = "localhost" #os.getenv("MARIADBHOST")
MARIADBPORT = "32100" #os.getenv("MARIADBPORT")
MARIADBUSER = "root" #os.getenv("MARIADBUSER")
MARIADBPASS = "IteAgY6fBV" #os.getenv("MARIADBPASS")
"""
# Enum for colors
class bcolors:
    PROCESSING  = '\33[96m'     #CYAN
    OK          = '\033[92m'    #GREEN
    WARNING     = '\033[93m'    #YELLOW
    FAIL        = '\033[91m'    #RED
    GRAY        = '\033[90m'    #GRAY
    RESET       = '\033[0m'     #RESET COLOR

# Class containing the programs logic
class SQLProcessor:
    __consumerQueue = None
    __publishQueue = None
    __elasticClient = None
    __mariaClient = None
    __currentJob = None
    __currentDoc = None
    __currentDocId = None
    __currentExpression = None
    __currentSqltransform = None
    __time = 0
    __processedGroups = 0
    __totalTimeMetric = None
    __avgTimeMetric = None
    __processedGroupsMetric = None

    def __init__(self):
        self.initQueues()
        self.initMetrics()
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

    # Simple method used to connect to an elasticsearch database
    def connectElastic(self,user,password,host,port):
        self.__elasticClient = Elasticsearch(
            host+":"+port,
            basic_auth=(user,password)
        )
        try:
            self.__elasticClient.info()
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
            # can't continue without a place to get
            # information to publish in elastic
            raise Exception("Error: Couldn't connect to MariaDB database")

    # Method to initialize consuming queue and the publishing queue
    def initQueues(self):
        rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
        rabbitParameters = pika.ConnectionParameters(
            heartbeat=120,
            blocked_connection_timeout=120,
            host=RABBITHOST,
            port=RABBITPORT,
            credentials=rabbitUserPass
        )
        try:
            self.__consumerQueue = pika.BlockingConnection(rabbitParameters).channel()
            self.__publishQueue = pika.BlockingConnection(rabbitParameters).channel()
            self.__consumerQueue.basic_qos(prefetch_count=1)
        except pika.exceptions.AMQPConnectionError:
            # We can't continue without a queue to get data from 
            # and to publish our results
            raise Exception("Error: Couldn't connect to RabbitMQ")
        self.__consumerQueue.queue_declare(queue=RABBITCONSUMEQUEUE)
        self.__publishQueue.queue_declare(queue=RABBITPUBLISHQUEUE)

        self.__consumerQueue.basic_consume(queue=RABBITCONSUMEQUEUE, on_message_callback=self.consume, auto_ack=False)

    def reconnectPublishQueue(self):
        #Creating parameters to rabbit
        rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
        rabbitParameters = pika.ConnectionParameters(
            heartbeat=120,
            blocked_connection_timeout=120,
            host=RABBITHOST,
            port=RABBITPORT,
            credentials=rabbitUserPass
        )
        #Connecting to RABBITMQ
        try:
            self.__publishQueue = pika.BlockingConnection(rabbitParameters).channel()
        except pika.exceptions.AMQPConnectionError as e:
            # We can't continue without a queue to publish our results
            print(f"{bcolors.FAIL} Error: {bcolors.RESET} Couldn't connect to RabbitMQ")
        #Creating queues
        self.__publishQueue.queue_declare(queue=RABBITPUBLISHQUEUE)

    # Method to initialize Prometheus metrics
    def initMetrics(self):
        self.__totalTimeMetric = Gauge(
            'sqlprocessor_total_processing_time', 
            'Total amount of time elapsed when processing'
        )
        self.__avgTimeMetric = Gauge(
            'sqlprocessor_avg_processing_time', 
            'Average amount of time elapsed when processing'
        )
        self.__processedGroupsMetric = Gauge(
            'sqlprocessor_number_processed_groups', 
            'Number of Groups process by SQL Processor'
        )
        self.__totalTimeMetric.set(0)
        self.__avgTimeMetric.set(0)
        self.__processedGroupsMetric.set(0)

    # This method retrieves the job and group document from elastic with the
    # recieved job_id and group_id of the queue
    def getFromElastic(self,message):
        success = False
        try:
            search = self.__elasticClient.search(index="jobs",size=1,query={"match" : {"job_id" : message["job_id"]}})
            self.__currentJob = search["hits"]["hits"][0]["_source"]
            for i in range(int(SQLPROCESSORRETRIES)):
                search = self.__elasticClient.search(index="groups",size=1,query={"match" : {"group_id" : message["group_id"]}})
                self.__currentDoc = search["hits"]["hits"][0]["_source"]
                self.__currentDocId = search["hits"]["hits"][0]["_id"]
                if("docs" in self.__currentDoc):
                    success = True
                    break
                sleep(int(SQLPROCESSORTIMEOUT))
            if(not success):
                print(
                    bcolors.FAIL + "Error:" + bcolors.RESET + " Group doesn't have docs in it -> " + bcolors.WARNING + "group_id:" + 
                    message["group_id"] + bcolors.RESET
                )
                return True
        except IndexError:
            # if we don't find any document, we can't continue
            print(
                bcolors.FAIL + "Error:" + bcolors.RESET + " Didn't find job or group -> " + bcolors.WARNING + "group_id:" + 
                message["group_id"] + " -> job_id: " + message["job_id"] + bcolors.RESET
            )
            return True
        return False
    
    # From the retrieved documents, we get the expression we need
    # to run for each JSON in the docs field
    def getExpression(self):
        sqltransform = None
        transform = None

        for stage in self.__currentJob["stages"]:
            if(stage["name"] == "transform"):
                transform = stage
                break
        
        if(transform == None):
            print(
                # If we didn't find a transform stage, we can't continue
                bcolors.FAIL + "Error:" + bcolors.RESET + " No transform in stages -> " + 
                bcolors.WARNING + self.__currentDoc["group_id"] + bcolors.RESET
            )
            return True
        
        for transformation in transform["transformation"]:
            if(transformation["type"] == "sql_transform"):
                sqltransform = transformation
                break

        if(sqltransform == None):
            # if we didn't find a sql_transform type of transformation, we can't continue
            print(
                bcolors.FAIL + "Error:" + bcolors.RESET + " No sql_transform type of transformation in the transform stage -> " + 
                + bcolors.WARNING + self.__currentDoc["group_id"] + bcolors.RESET
            )
            return True
        
        self.__currentExpression = sqltransform["expression"]
        self.__currentSqltransform = sqltransform
        return False
    
    # before executing the expression obtain in the last step, we need to change some
    # variables in it found on "fields_mapping" and we need to put which table
    # we are getting data from.
    def processExpression(self):
        fieldsRegex = "(?<=%{)\\b(?!table\\b)\\b(?!doc_field\\b)[a-zA-Z0-9_]*(?=}%)"
        fields = Regex.findall(fieldsRegex,self.__currentExpression)
        self.__currentExpression = self.__currentExpression.replace(
            "%{table}%",
            self.__currentSqltransform["table"]
        )

        for field in fields:
            if(field == "table" or field == "doc_field"):
                continue
            if(field not in self.__currentSqltransform["fields_mapping"]):
                # Without fields_mappings, we can't replace variables
                print(bcolors.FAIL + "Error: " + bcolors.RESET + "missing field_mappings")
                return True
            self.__currentExpression = self.__currentExpression.replace(
                "%{"+ field +"}%",
                self.__currentSqltransform["fields_mapping"][field]
            )

        return False

    # last step in the SQL Processor, here we get
    # the docs list and execute the expression to add
    # a new field with the retrieve data.
    def changeDocs(self):
        docField = self.__currentSqltransform["doc_field"]
        docs = self.__currentDoc["docs"]

        # There wasn't any specific way to get the field name
        # so, we get it from the table we are searching in.
        fieldname = Regex.findall(
            "(?<=SELECT )[a-zA-Z0-9_]*",
            self.__currentExpression
        )[0]
        cursor = self.__mariaClient.cursor()
        try:
            for doc in docs:
                cursor.execute(
                    self.__currentExpression.replace(
                        "%{doc_field}%",
                        str(doc[docField])
                    )
                )
                result = cursor.fetchone()
                if(result is not None):
                    doc[fieldname] = result[0]
        except mariadb.ProgrammingError:
            # There is the possibility the expression fails, so we handle that error
            print(
                bcolors.FAIL + "Error: " + bcolors.RESET + "root.stages[name=transform].transformation[type=sql_transform].expression \
                failed, document -> " + bcolors.WARNING + self.__currentDoc["group_id"] + bcolors.RESET
            )
            return True
        
        
        self.__currentDoc["docs"] = docs
        self.__elasticClient.index(index="groups",id=self.__currentDocId,document=self.__currentDoc)
        return False

    #Publish to the queue the new message
    def produce(self, message):
        try:
            self.__publishQueue.basic_publish(routing_key=RABBITPUBLISHQUEUE, body=message, exchange='')
        except pika.exceptions.StreamLostError:
            print(f"{bcolors.FAIL} Error: {bcolors.RESET} connection lost, reconnecting... ")
            self.reconnectPublishQueue()
            self.produce(message)

    # Method used as callback for the consume
    def consume(self, ch, method, properties, msg):
        
        startTime = time()
        message = json.loads(msg)
        print(
            bcolors.OK + "Message Receive: " + bcolors.RESET + "Starting Process -> " +
            bcolors.GRAY + str(message) + bcolors.RESET
        )
        if(self.getFromElastic(message)):
            ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
            return
        print(
            bcolors.PROCESSING + "Processing: " + bcolors.RESET + "Group and Job found" +
            bcolors.RESET
        )
        if(self.getExpression()):
            ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
            return
        print(
            bcolors.PROCESSING + "Processing: " + bcolors.RESET + "expression obtained -> " +
            bcolors.GRAY + str(self.__currentExpression) + bcolors.RESET
        )
        if(self.processExpression()):
            ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
            return
        print(
            bcolors.PROCESSING + "Processing: " + bcolors.RESET + "expression variables proccesed -> " +
            bcolors.GRAY + str(self.__currentExpression) + bcolors.RESET
        )
        if(self.changeDocs()):
            ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
            return
        print(
            bcolors.PROCESSING + "Processing: " + bcolors.RESET + "Docs changed and published" +
            bcolors.RESET
        )
        self.produce(msg)
        print(bcolors.OK + "Group finished:" + bcolors.RESET + " -> " + bcolors.GRAY + self.__currentDoc["group_id"] + bcolors.RESET)

        self.__time += (time() - startTime)
        self.__processedGroups += 1
        self.__processedGroupsMetric.set(self.__processedGroups)
        self.__totalTimeMetric.set(self.__time)
        self.__avgTimeMetric.set(self.__time/self.__processedGroups)

        ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)

    def startProcess(self):
        start_http_server(6941)
        self.__consumerQueue.start_consuming()

processor = SQLProcessor()
processor.startProcess()