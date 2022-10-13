import pika
import json
# RabbitMQ
RABBITHOST = "localhost" #os.getenv("RABBITHOST")
RABBITPORT = "30100" #os.getenv("RABBITPORT")
RABBITUSER = "user" #os.getenv("RABBITUSER")
RABBITPASS = "XQnpNkb23Z5RqAly" #os.getenv("RABBITPASS")
RABBITCONSUMEQUEUE = "mysqlprocessor" #os.getenv("RABBITQUEUENAME")
RABBITPUBLISHQUEUE = "sqlprocessor" #os.getenv("RABBITQUEUENAME")

document = {
    "job_id" : "nuevo28392",
    "group_id" : "nuevo28392-100"
}

rabbitUserPass = pika.PlainCredentials(RABBITUSER,RABBITPASS)
rabbitParameters = pika.ConnectionParameters(
    heartbeat=120,
    blocked_connection_timeout=120,
    host=RABBITHOST,
    port=RABBITPORT,
    credentials=rabbitUserPass
)

cola = pika.BlockingConnection(rabbitParameters).channel()

cola.basic_publish(routing_key=RABBITCONSUMEQUEUE, body=json.dumps(document), exchange= '')