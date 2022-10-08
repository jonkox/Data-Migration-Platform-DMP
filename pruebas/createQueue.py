"""
Prueba para crear una cola de rabbitmq y publicar un mensaje
"""

import pika
import os

# Create a connection, localhost can be changed if needed'
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

QUEUE_NAME = 'root.stages[name=load].source_queue'

# Create a queue
channel.queue_declare(queue = QUEUE_NAME)


# msg = open(os.path.join(__location__, 'msg.json'))
# channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=msg)

my_local_file = os.path.join(os.path.dirname(__file__), 'msg.json')
f = open(my_local_file,  "r")
my_local_data = f.read()
channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=my_local_data)

print(" [x] Sent JSON message")

connection.close()