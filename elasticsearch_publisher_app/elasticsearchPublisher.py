import json
import pika
import elasticsearch
import os

from elasticsearch import Elasticsearch

def workForPod(jsonObject):
    # en el server de ES root.control_data_source
        # Buscar en el indice groups
            # obtener el documento del grupo identificado por group_id 
    
    # Obtener el group_id del mensaje recibido
    print(jsonObject["group_id"])

    #serverReceive = client.get(index="groups", id=1)
    
    # Mismo server
        # buscar en el indice jobs
            # el documento del job representado por job_id

    # por cada documento en el campo docs
        # se publica en el indice root.stages[name=load]. index_name
            # del servidor root.stages[name=load].destination_data_source
    
    # cuando termine de publicar, se elimina el documento del indice groups
        # del servidor root.control_data_source


# Revisar la cola de rabbitmq
def callback(ch, method, properties, body):
    #json_object = json.load(body)
    #resp = client.index(index = ESINDEX, id = hashlib.md5(body).hexdigest(), document = json_object)
    #print(resp)
    print(" [x] Received %r" % body)
 
    json_object = json.loads(body)
    workForPod(json_object)

QUEUE_NAME = 'root.stages[name=load].source_queue'
ESENDPOINT = "root.control_data_source"

client = Elasticsearch("http://localhost:32500")

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()
channel.basic_consume(queue= QUEUE_NAME, auto_ack=True, on_message_callback=callback)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)