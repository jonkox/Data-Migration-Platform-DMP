from elasticsearch import Elasticsearch
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

class SQLProcessor:
    __consumerQueue = None
    __publishQueue = None

    def __init__(self):
        self.initQueues()

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
        print(message)

    def startProcess(self):
        self.__consumerQueue.start_consuming()

processor = SQLProcessor()
processor.startProcess()