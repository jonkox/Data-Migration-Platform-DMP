from prometheus_client import Gauge, start_http_server
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

#----------------------------------------------------------------------- 
# Class for printing colors
#----------------------------------------------------------------------- 
class bcolors:
    OK      = '\033[92m'    #GREEN
    WARNING = '\033[93m'    #YELLOW
    FAIL    = '\033[91m'    #RED
    RESET   = '\033[0m'     #RESET COLOR
    
#----------------------------------------------------------------------- 
#Main class
#----------------------------------------------------------------------- 
class MySQLConnector:
    
    ElasticClient = None
    MariaClient = None

    # Metrics
    TIME_ = 0
    PROCESSGROUPS_ = 0
    TOTAL_TIME = None
    AVG_TIME = None
    NUMBER_PROCESSEDGROUPS = None

    def __init__(self):
        self.startMetrics()
        self.connectDbElastic(ELASTICHOST,ELASTICPORT,ELASTICUSER,ELASTICPASS)
        self.startConsume(RABBITUSER,RABBITPASS,RABBITHOST,RABBITPORT,RABBITQUEUENAME)
        
    #----------------------------------------------------------------------- 
    # Function that creates an elastic client
    #----------------------------------------------------------------------- 
    def connectDbElastic(self,pHost,pPort,pUser,pPass):
        try:
            self.ElasticClient = Elasticsearch(
                    pHost+":"+pPort,
                    basic_auth=(pUser,pPass)
                )
        except elastic_transport.ConnectionError:
            raise Exception ("Error: Couldn't connect to database Elastic")
            
    #-----------------------------------------------------------------------         
    # Function that creates an maria client
    #----------------------------------------------------------------------- 
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
            
    #-----------------------------------------------------------------------        
    # Setting metrics and start server for metrics
    #----------------------------------------------------------------------- 
    def startMetrics(self):    
        self.TOTAL_TIME = Gauge(
            'total_processing_time', 
            'Total amount of time elapsed when processing'
        )

        self.AVG_TIME = Gauge(
            'avg_processing_time', 
            'Average amount of time elapsed when processing'
        )

        self.NUMBER_PROCESSEDGROUPS = Gauge(
            'number_processed_groups', 
            'Number of Jobs process by MySQLConnector'
        )
        
        self.TOTAL_TIME.set(0)
        self.AVG_TIME.set(0)
        self.NUMBER_PROCESSEDGROUPS.set(0)

        start_http_server(6945)
        
    #-----------------------------------------------------------------------    
    # Function that opens channel and consumes message sent by orchestrator
    #-----------------------------------------------------------------------
    def startConsume(self,pUser,pPass,pHost,pPort,pQueue):
        credentials_ = pika.PlainCredentials(pUser, pPass)
        parameters = pika.ConnectionParameters(host=pHost, port=pPort, credentials=credentials_)
        connection = pika.BlockingConnection(parameters)
        channelConsuming = connection.channel()
        channelConsuming.basic_qos(prefetch_count=1)
        channelConsuming.queue_declare(queue=pQueue)
        channelConsuming.basic_consume(queue=pQueue, on_message_callback= self.callback, auto_ack=False)

        channelConsuming.start_consuming()
        
    #----------------------------------------------------------------------- 
    # Function that opens channel and sends message to the second queue
    #----------------------------------------------------------------------- 
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
        
    #----------------------------------------------------------------------- 
    # Function that converts the orchestrator message to a json object, 
    # works with that object and updates metrics
    #----------------------------------------------------------------------- 
    def callback (self, ch, method, properties, body):
        sleep(1) #
        json_msg = json.loads(body)

        startTime = time() 

        self.work(json_msg,body)

        #Updating metrics
        self.TIME_ += (time() - startTime)
        self.PROCESSGROUPS_ += 1
        self.NUMBER_PROCESSEDGROUPS.set(self.PROCESSGROUPS_)
        self.TOTAL_TIME.set(self.TIME_)
        self.AVG_TIME.set(self.TIME_/self.PROCESSGROUPS_)

        ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
        print(f"{bcolors.OK} MySQL Connector: {bcolors.RESET} Process finished")

    #----------------------------------------------------------------------- 
    # Main function of the application where it works with the message.
    #----------------------------------------------------------------------- 
    def work(self, pMsg, pBody):
        print(f"{bcolors.OK} MySQL Connector: {bcolors.RESET} Process started")
        #We look in the jobs index for the recent json document and we get the document
        json_job = self.ElasticClient.search(index='jobs',size=1,query={"match":{"job_id":pMsg["job_id"]}})
        idDocumento = json_job["hits"]["hits"][0]["_id"] 
        loadJson = self.ElasticClient.get(index="jobs", id=idDocumento)["_source"]
        groupId=pMsg["group_id"] 
        jobid = pMsg["job_id"]   
        
        #---------> Data to make the query, we get it from the loaded document
        expresion = loadJson["source"]["expression"] #The select you should execute on the database   
        groupSize = loadJson["source"]["grp_size"] 
        startRow = groupId[self.counterWord(groupId):] 
        query = expresion+" LIMIT "+startRow+","+groupSize #Final query
        
        #---------> In this part, the final query is made to MariaDB and once the result is transformed into a list
        json_output = self.transformacion (query, (groupSize,))
        documentUpdate = self.ElasticClient.search(index='groups',size=1,query={"match":{"group_id":groupId}})
        
        #---------> Update to elastic
        self.update(documentUpdate,jobid,groupId,json_output)
        
        #---------> When all the work is done, we publish to the second queue
        self.startProduce(RABBITUSER,RABBITPASS,RABBITHOST,RABBITPORT,RABBITQUEUEMYSQL,pBody)

    def update(self, pDoc, pJobId, pGrpId, pJson):
        try:
            idHit = pDoc["hits"]["hits"][0]["_id"]
            data = {"job_id": pJobId, "group_id": pGrpId, 'docs': pJson} #Added fiel docs
            self.ElasticClient.index(index='groups', id=idHit,body=data) #Overwrite document
        except Exception as e:
            print("Error. Can't update " + str(e))
            
    #----------------------------------------------------------------------- 
    # This function connects to MariaDb, makes the query and transforms that query to a list of type key : value
    # Return that transformation
    #----------------------------------------------------------------------- 
    def transformacion(self, query, args=(), one=False):
        self.connectDbMaria(MARIADBHOST,MARIADBPORT,MARIADBUSER,MARIADBPASS,MARIADBNAME) 
        try:
            cur = self.MariaClient.cursor()
            cur.execute(query, args)
        except mariadb.Error as error:
            print("Error in query: {}".format(error))
        queryResult = [dict((cur.description[i][0], value) \
                for i, value in enumerate(row)) for row in cur.fetchall()]
        cur.connection.close()
        return (queryResult[0] if queryResult else None) if one else queryResult
    
    #----------------------------------------------------------------------- 
    # Count the letters to - 
    # For example: Orchestrator sends a message with a key group_id and its value 
    # is of type jobid-number. We need to count the letters up to the hyphen in order to get the number
    #----------------------------------------------------------------------- 
    def counterWord(self, pWord):
        control = 0
        for i in pWord:
            control += 1
            if i == "-":
                return control
MySQLConnector()     
