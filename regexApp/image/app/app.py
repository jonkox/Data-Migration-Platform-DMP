from    elasticsearch       import      Elasticsearch
from    time                import      sleep,time
from    prometheus_client   import      Gauge,start_http_server
from    datetime            import      datetime

import os
import re
import json
import pika
import elastic_transport


#---------------------------------------------------------------------------------------------------------------------------------------------
# ENVIRONMENT VARIABLES
#---------------------------------------------------------------------------------------------------------------------------------------------


# Elasticsearch
ELASTICHOST         =   os.getenv("ELASTICHOST")
ELASTICPORT         =   os.getenv("ELASTICPORT")
ELASTICUSER         =   os.getenv("ELASTICUSER")
ELASTICPASS         =   os.getenv("ELASTICPASS")

# RabbitMQ
RABBITHOST          =   os.getenv("RABBITHOST")
RABBITPORT          =   os.getenv("RABBITPORT")
RABBITUSER          =   os.getenv("RABBITUSER")
RABBITPASS          =   os.getenv("RABBITPASS")
SOURCEQUEUE         =   os.getenv("SOURCEQUEUE")
DESTQUEUE           =   os.getenv("DESTQUEUE")



#---------------------------------------------------------------------------------------------------------------------------------------------
# GLOBAL VARIABLES
#---------------------------------------------------------------------------------------------------------------------------------------------

"""
#ELASTICSEACH
ELASTICHOST         =   "http://localhost"  #os.getenv("ELASTICHOST")
ELASTICPORT         =   "32500"             #os.getenv("ELASTICPORT")
ELASTICPASS         =   "RYcgQ5MSpmjeRcjj"  #os.getenv("ELASTICPASS")
ELASTICUSER         =   "elastic"

#RABBITMQ
RABBITHOST          =   "localhost"         #os.getenv("RABBITHOST")
RABBITPORT          =   "30100"             #os.getenv("RABBITPORT")
RABBITUSER          =   "user"              #os.getenv("RABBITUSER")
RABBITPASS          =   "4VysVe8DAtHWUgit"  #os.getenv("RABBITPASS")
RABBITQUEUENAME     =   "REGEX-FUENTE"      #os.getenv("RABBITQUEUENAME")
SOURCEQUEUE         =   "regex_queue"       #Name of the queue that the application need to consume
DESTQUEUE           =   "ready"             #Name of the queue that the application need to produce
"""

#---------------------------------------------------------------------------------------------------------------------------------------------
# CLASSES
#---------------------------------------------------------------------------------------------------------------------------------------------


class bcolors:
    OK      = '\033[92m'    #GREEN
    WARNING = '\033[93m'    #YELLOW
    FAIL    = '\033[91m'    #RED
    RESET   = '\033[0m'     #RESET COLOR



class RegexProcessor:


    docs                =   []      #List of documents thas has been transform
    REGEX               =   None    #Regular expression taken from the job document
    FIELD               =   None    #Field where the REGEX has to be applied
    NEWFIELD            =   None    #New field that need to be created into the document
    INITIALRESPONSE     =   None    #Gets the jobs from the index jobs
    JOB                 =   None    #Just one job at the time, has all the config file
    PUBLISHQUEUE        =   None    #Queue where the application needs to consume
    CONSUMERQUEUE       =   None    #Destination queue, ehre the applications need to produce
    SIZE                =   None    #Size of the partition based on the job document
    DOCID               =   None    #Job id, not the fiel "job_id", it's own ID
    ACTUALMESSAGE       =   None    #Most recent message taken from the queue
    ELASTICCLIENT       =   None    #Connection to ElasticSearch
    TIME                =   0       #Time that a group has been processed
    PROCESSGROUPS       =   0       #Quantity of groups that has been processed
    TOTALTIME           =   None    #Total time the app has processed
    AVGTIME             =   None    #Average time process per group
    PROCESSEDGROUPS     =   None    #Total quantity of groups has been processed


    #Constructor method
    def __init__(self):

        #Initialize metrics variables
        self.TOTALTIME = Gauge(
            'total_processing_time', 
            'Total amount of time elapsed when processing'
        )

        self.AVGTIME = Gauge(
            'avg_processing_time', 
            'Average amount of time elapsed when processing'
        )

        self.PROCESSEDGROUPS = Gauge(
            'number_processed_groups', 
            'Number of Jobs process by REGEX Processor'
        )
        
        #Setting metrics variables
        self.TOTALTIME.set(0)
        self.AVGTIME.set(0)
        self.PROCESSEDGROUPS.set(0)

        #Starting server where we send metrics
        start_http_server(6943)

        #Initialize process
        self.connectElastic(ELASTICUSER,ELASTICPASS,ELASTICHOST,ELASTICPORT)
        self.initQueues()
        self.startProcess()

    #Initialize queues, it creates source and destination queue to the processor
    def initQueues(self):
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
            self.CONSUMERQUEUE = pika.BlockingConnection(rabbitParameters).channel()
            self.PUBLISHQUEUE = pika.BlockingConnection(rabbitParameters).channel()
            self.CONSUMERQUEUE.basic_qos(prefetch_count=1)
        except pika.exceptions.AMQPConnectionError:
            # We can't continue without a queue to publish our results
            raise Exception("Error: Couldn't connect to RabbitMQ")
        
        #Creating queues
        self.CONSUMERQUEUE.queue_declare(queue=SOURCEQUEUE)
        self.PUBLISHQUEUE.queue_declare(queue=DESTQUEUE)

        self.CONSUMERQUEUE.basic_consume(queue=SOURCEQUEUE, on_message_callback=self.consume, auto_ack=False)
        

    # Simple method used to connect to an elasticsearch database
    def connectElastic(self,user,password,host,port):
        URL = f"{host}:{port}"
        try:
            self.ELASTICCLIENT = Elasticsearch(URL,basic_auth=(user,password))
        except elastic_transport.ConnectionError:
            raise Exception("Error: Couldn't connect to database")
    
    #Method to close connection to ElasticSearch
    def closeElastic(self):
        self.__elasticClient.close()

    #Get Field Info takes all necessary info to the processor from the job that it's been processed
    def getFieldsInfo(self, jobId):
        #Initial response it's the initial result from a query to ES
        self.INITIALRESPONSE = self.ELASTICCLIENT.search(query={"bool": {"must": [{"match": {"_index": "jobs"}},{"match": {"job_id": jobId}}]}})
        

        self.JOB = self.INITIALRESPONSE["hits"]["hits"][0]["_source"]
        self.SIZE = self.JOB["source"]["grp_size"]

        for i in self.JOB["stages"]:
            if i["name"] == "transform":#asks if it has some stage.transform
                for j in i["transformation"]: #if it does, it takes the info from regex_transform
                    if j["type"] == "regex_transform":
                        self.NEWFIELD       = j["field_name"]
                        self.FIELD          = j["regex_config"]["field"]
                        self.REGEX          = j["regex_config"]["regex_expression"]

    #Transform makes all the transformation process
    def transform(self, groupId):
        
        #Search for the group given by parameter
        query = self.ELASTICCLIENT.search(index="groups",size="1",query={"match" : {"group_id":groupId}})
        query = query["hits"]["hits"][0]
        self.DOCID = query["_id"]   #Takes it's ID and save to the moment when we need to re-write the document


        #Cycle to transform every doc in the group
        dat = []
        for j in range(int(self.SIZE)):
            match = re.findall(self.REGEX,query["_source"]["docs"][j][self.FIELD])
            if match:
                dato = query["_source"]["docs"][j]
                dato[self.NEWFIELD] = match[0]
                dat.append(dato)

        #Create the new doc taking the info that comes and adding the new field
        doc = {
        "job_id" : query["_source"]["job_id"],
        "group_id": query["_source"]["group_id"],
        "docs": dat
        }

        #Write the new doc into ES
        self.ELASTICCLIENT.index(index="groups", id=self.DOCID, document=doc)
        print(f"{bcolors.OK} REGEX PROCESSOR: {bcolors.RESET} Transformation Complete [{str(datetime.today().strftime('%A, %B %d, %Y %H:%M:%S'))}]")

    #Publish to the queue the new message
    def produce(self, message):
        self.PUBLISHQUEUE.basic_publish(routing_key=DESTQUEUE, body=json.dumps(message), exchange='')
    
    #Aux method, it's called by consuming process, it takes the message and sends to the processor to be processed
    #It also update metrics
    def consume(self, ch, method, properties, msg):
        message = json.loads(msg)

        print(f"{bcolors.OK} REGEX PROCESSOR: {bcolors.RESET} Process Started [{str(datetime.today().strftime('%A, %B %d, %Y %H:%M:%S'))}]")

        sleep(1)

        startTime = time()      #taking initial time before processing start

        #Processing Process
        self.getFieldsInfo(message["job_id"])
        self.transform(message["group_id"])
        self.produce(message)

        #Updating metrics
        self.TIME += (time() - startTime)
        self.PROCESSGROUPS += 1
        self.PROCESSEDGROUPS.set(self.PROCESSGROUPS)
        self.TOTALTIME.set(self.TIME)
        self.AVGTIME.set(self.TIME/self.PROCESSGROUPS)

        
        print(f"{bcolors.OK} REGEX PROCESSOR: {bcolors.RESET} Process Finished [{str(datetime.today().strftime('%A, %B %d, %Y %H:%M:%S'))}]")
        ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)


    #Method that constantly checks queue waiting for new messages
    def startProcess(self):
        self.CONSUMERQUEUE.start_consuming()



RegexProcessor()

