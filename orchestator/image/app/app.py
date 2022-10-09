from math import ceil
from enum import Enum
from time import sleep
from elasticsearch import Elasticsearch
import elastic_transport
import mariadb
import os

# Environmental Variables
ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "" #os.getenv("ELASTICUSER")
ELASTICPASS = "" #os.getenv("ELASTICPASS")
MARIADBNAME = "my_database" #os.getenv("MARIADBNAME")

# Enumeration for type of elasticsearch database
# DEST -> "control_data_source" found in a job document
# JOBS -> initial elasticsearch database to wait for jobs
class ElasticClientType(Enum):
    DEST = 0
    JOBS = 1

# Class containing all the orchestrator process
class Orchestrator:
    __groupCount = 0
    __groupSize = 0
    __elasticClientJobs = None
    __elasticClientDest = None
    __mariaClient = None
    __jobDocument = None
    __jobDocumentId = None
    
    # First of all we want to connect to the elasticsearch job database
    # to wait for jobs
    def __init__(self):
        self.connectElastic(ELASTICUSER,ELASTICPASS,ELASTICHOST,ELASTICPORT)

    # Simple method used to connect to an elasticsearch database
    def connectElastic(self,user,password,host,port,type=ElasticClientType.JOBS):
        if(type == ElasticClientType.JOBS):
            self.__elasticClientJobs = Elasticsearch(
                host+":"+port,
                basic_auth=(user,password)
            )
            try:
                self.__elasticClientJobs.info()
                return True
            except elastic_transport.ConnectionError:
                # We raise an exception an exception because the process 
                # can't continue without a place to look for jobs
                raise Exception("Error: Couldn't connect to Jobs database")
        else:
            self.__elasticClientDest = Elasticsearch(
                host+":"+port,
                basic_auth=(user,password)
            )
            try:
                self.__elasticClientDest.info()
                return True
            except elastic_transport.ConnectionError:
                print(
                "Error: Couldn't connect to an Elasticsearch database, document -> " \
                + self.__jobDocument["job_id"]
                )
                self.failedFile() 
        return False
        
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
            print(
                "Error: Couldn't connect to a MySQl database, documento -> " \
                + self.__jobDocument["job_id"]
            )
            self.failedFile()

    # Method for closing MariaDB       
    def closeMariadb(self):
        if(self.__mariaClient != None):
            self.__mariaClient.close()
    
    # Method for closing Elasticsearch  
    def closeElastic(self):
        if(self.__elasticClientDest != None):
            self.__elasticClientDest.close()

    # Method for the starting process
    def startProcess(self):
        # we want to make sure we have a place to look for jobs and to store groups
        if(not (self.__elasticClientJobs.indices.exists(index=["jobs"]))):
            self.__elasticClientJobs.indices.create(index="jobs")
        if(not (self.__elasticClientJobs.indices.exists(index=["groups"]))):
            self.__elasticClientJobs.indices.create(index="groups")
        
        # Making sure pod stays up by providing a infinite loop
        while True:
            sleep(1) # To avoid to filling up elasticsearch with requests, we wait some time

            # Searching process for a new job
            search = self.__elasticClientJobs.search(index="jobs",size="1",query={"match" : {"status":"new"}})
            if(search["hits"]["hits"]):
                self.__jobDocumentId = search["hits"]["hits"][0]["_id"]
                self.__jobDocument = self.__elasticClientJobs.get(index="jobs",id=self.__jobDocumentId)["_source"]
                self.__jobDocument["status"] = "In-process"
                self.__elasticClientJobs.index(index="jobs",id=self.__jobDocumentId,document=self.__jobDocument)
                if(self.getGroupCount() == True):
                    continue # we want to skip the next step some thing fails before it
                self.createDocs()
                print("Finished job -> " + self.__jobDocument["job_id"])
        
    # given a source name, we find the JSON with the access to a MySQL type database
    def getMySQLDataSource(self,sourceName):
        sources = self.__jobDocument["data_sources"]
        for source in sources:
            if(source["name"] == sourceName and \
            source["type"] == "mysql"):
                return source
        return None

    # given a source name, we find the JSON with the access to a Elasticsearch type database
    def getElasticDataSource(self,sourceName):
        sources = self.__jobDocument["data_sources"]
        for source in sources:
            if(source["name"] == sourceName and \
            source["type"] == "elasticsearch"):
                return source
        return None

    # before creating any group document, we need to know 
    # the amount of groups/documents we want to create
    # this is the first step in the orchestrator
    def getGroupCount(self):
        source = self.getMySQLDataSource(self.__jobDocument["source"]["data_source"])

        if(source == None):
            print(
                "Error: data_source is not 'mysql' type, document -> " \
                + self.__jobDocument["job_id"]
            )
            self.failedFile()
            return True
        
        self.connectMariadb(
            source["usuario"],
            source["password"],
            source["url"],
            source["port"]
        )

        try:
            self.__groupSize = int(self.__jobDocument["source"]["grp_size"])
        except TypeError:
            print(
                "Error: root.source.gpr_size must be a number, document -> " \
                + self.__jobDocument["job_id"]
                )
            self.failedFile()
            self.closeMariadb()
            return True

        cursor = self.__mariaClient.cursor()

        cursor.execute("SELECT Count(1) FROM persona")
        self.__groupCount = ceil(cursor.fetchone()[0]/self.__groupSize)

        cursor.close()

        self.closeMariadb()

    # Next step is to create the JSON documents with job_id and 
    # group_id with different offsets, this method is in charge of that.
    def createDocs(self):
        source = self.getElasticDataSource(self.__jobDocument["control_data_source"])

        if(source == None):
            print(
                "Error: destination_data_source is not 'elasticsearch' type, document -> " \
                + self.__jobDocument["job_id"]
            )
            self.failedFile()
            return

        if(not self.connectElastic(
            source["usuario"],
            source["password"],
            source["url"],
            source["port"],
            type=ElasticClientType.DEST
        )):
            return

        for offset in range(0,self.__groupCount):
            groupDocument = {
                "job_id" : self.__jobDocument["job_id"],
                "groud_id" : self.__jobDocument["job_id"] + "-" + str(self.__groupSize*offset) 
            }
            self.__elasticClientDest.index(index="groups",document=groupDocument)
        
        self.closeElastic()

    # This method is very simple, if we managed to get an error without the pod failing
    # we "mark" that job with a "Failed" status, so it is easier to identify bad jobs
    def failedFile(self):
        self.__jobDocument["status"] = "Failed"
        self.__elasticClientJobs.index(index="jobs",id=self.__jobDocumentId,document=self.__jobDocument)

# program initiation
orquestador = Orchestrator()
orquestador.startProcess()

