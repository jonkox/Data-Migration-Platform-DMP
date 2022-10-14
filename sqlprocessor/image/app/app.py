from elasticsearch import Elasticsearch
import re as Regex
import elastic_transport
import mariadb
import json
import pika


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

    def __init__(self):
        self.initQueues()
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
            # can't continue without a place to look get
            # information to publish in elastic
            raise Exception("Error: Couldn't connect to MariaDB database")

    def getFromElastic(self,message):
        search = self.__elasticClient.search(index="jobs",size=1,query={"match" : {"job_id" : message["job_id"]}})
        self.__currentJob = search["hits"]["hits"][0]["_source"]
        search = self.__elasticClient.search(index="groups",size=1,query={"match" : {"group_id" : message["group_id"]}})
        self.__currentDoc = search["hits"]["hits"][0]["_source"]
        self.__currentDocId = search["hits"]["hits"][0]["_id"]

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
        except pika.exceptions.AMQPConnectionError:
            # We can't continue without a queue to publish our results
            raise Exception("Error: Couldn't connect to RabbitMQ")
        self.__consumerQueue.queue_declare(queue=RABBITCONSUMEQUEUE)
        self.__publishQueue.queue_declare(queue=RABBITPUBLISHQUEUE)

        self.__consumerQueue.basic_consume(queue=RABBITCONSUMEQUEUE, on_message_callback=self.consume, auto_ack=True)

    def consume(self, ch, method, properties, msg):
        message = json.loads(msg)
        self.getFromElastic(message)
        self.getExpression()
        self.processExpression()
        self.changeDocs()
        self.__publishQueue.basic_publish(routing_key=RABBITPUBLISHQUEUE, body=msg, exchange='')
        print("Group finished -> " + self.__currentDoc["group_id"])
    
    def getExpression(self):
        sqltransform = None
        transform = None

        for stage in self.__currentJob["stages"]:
            if(stage["name"] == "transform"):
                transform = stage
                break
        
        if(transform == None):
            print(
                "Error: No transform in stages -> " + 
                self.__currentDoc["group_id"]
            )
            return True
        
        for transformation in transform["transformation"]:
            if(transformation["type"] == "sql_transform"):
                sqltransform = transformation
                break

        if(sqltransform == None):
            print(
                "Error: No sql_transform type of transformation in the transform stage -> " + 
                self.__currentDoc["group_id"]
            )
            return True
        
        self.__currentExpression = sqltransform["expression"]
        self.__currentSqltransform = sqltransform
        return False
        
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
                print("Error: missing field_mappings")
                return True
            self.__currentExpression = self.__currentExpression.replace(
                "%{"+ field +"}%",
                self.__currentSqltransform["fields_mapping"][field]
            )

        return False

    def changeDocs(self):
        docField = self.__currentSqltransform["doc_field"]
        docs = self.__currentDoc["docs"]
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
                doc[fieldname] = cursor.fetchone()[0]
        except mariadb.ProgrammingError:
            print(
                "Error: root.stages[name=transform].transformation[type=sql_transform].expression \
                failed, document -> " + self.__currentDoc["group_id"]
            )
            return True
        
        self.__currentDoc["docs"] = docs
        self.__elasticClient.index(index="groups",id=self.__currentDocId,document=self.__currentDoc)
        return False



    def startProcess(self):
        self.__consumerQueue.start_consuming()

processor = SQLProcessor()
processor.startProcess()