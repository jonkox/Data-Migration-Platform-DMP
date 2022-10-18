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

# Class for printing colors
class bcolors:
    OK      = '\033[92m'    #GREEN
    WARNING = '\033[93m'    #YELLOW
    FAIL    = '\033[91m'    #RED
    RESET   = '\033[0m'     #RESET COLOR

#main class
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
        channelConsuming.queue_declare(queue=RABBITQUEUENAME)
        channelConsuming.basic_consume(queue=RABBITQUEUENAME, on_message_callback= self.callback, auto_ack=True)
        channelConsuming.start_consuming()

    def startProduce(self,pUser,pPass,pHost,pPort,pQueue,pMsg):
        print(f"{bcolors.OK} Mensaje que envia--->: {bcolors.RESET}",pMsg)
        credentials2 = pika.PlainCredentials(pUser, pPass)
        parameters2 = pika.ConnectionParameters(host=pHost, port=pPort, credentials=credentials2) 
        connection2 = pika.BlockingConnection(parameters2)
        channel2 = connection2.channel()
        channel2.queue_declare(queue=RABBITQUEUEMYSQL)
        msg2 =pMsg
        channel2.basic_publish(exchange='', routing_key=RABBITQUEUEMYSQL, body=msg2) 
        connection2.close()

    def callback (self, ch, method, properties, body):
        sleep(1) 
        print(f"{bcolors.OK} Mensaje que entra---> {bcolors.RESET}",body)
        json_msg = json.loads(body)
        self.work(json_msg,body)

    def work(self, pMsg, pBody):
        try:
            json_job = self.ElasticClient.search(index='jobs',size=1,query={"match":{"job_id":pMsg["job_id"]}}) 
            idDocumento = json_job["hits"]["hits"][0]["_id"] 
            loadJson = self.ElasticClient.get(index="jobs", id=idDocumento)["_source"]
        except:
            print("Error en el index")
        try:
            groupId=pMsg["group_id"] 
            jobid = pMsg["job_id"]    
        except:
            print("Error obteniendo el group_id o el jobid")
        #_____________________Datos para hacer consulta_______________________
        expresion = loadJson["source"]["expression"] #El select que debe ejecutar en la base de datos    
        groupSize = loadJson["source"]["grp_size"]  
        startRow = groupId[self.counterWord(groupId):]  
        query = expresion+" LIMIT "+startRow+","+groupSize
        #____________________Consultar y transformar__________________________  
        json_output = self.transformacion (query, (groupSize,))
        documentUpdate = self.ElasticClient.search(index='groups',size=1,query={"match":{"group_id":groupId}})
        #____________________Inicio de la actualizacion___________________________
        self.update(documentUpdate,jobid,groupId,json_output)
        #___________________Publicamos en la segunda cola________________________
        self.startProduce(RABBITUSER,RABBITPASS,RABBITHOST,RABBITPORT,RABBITQUEUEMYSQL,pBody)

    def update(self, pDoc, pJobId, pGrpId, pJson):
        sleep(10)
        try:
            idHit = pDoc["hits"]["hits"][0]["_id"]
            data = {"job_id": pJobId, "group_id": pGrpId, "docs":pJson} #Se annade del fiel docs
            self.ElasticClient.index(index='groups', id=idHit,document=data) #Sobreescribo documento
        except:
            print("Error. Can't update")

    def transformacion (self, query, args=(), one=False):
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

    def counterWord(self, pWord):
        control = 0
        for i in pWord:
            control += 1
            if i == "-":
                return control
MySQLConnector() 
