"""
Controlador para prueba unitaria del elasticsearch publisher app
"""

import pika
import elasticsearch
import os

from elasticsearch import Elasticsearch
from time import sleep,time

ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICUSER = "elastic" #os.getenv("ELASTICUSER")
ELASTICPASS = "m2Hl6qYVLMNFDfdZ" #cambiar contraseña si se desinstala #os.getenv("ELASTICPASS")

# Crea la instancia de un cliente
ESConnection = Elasticsearch(
    ELASTICHOST+":"+ELASTICPORT,
    basic_auth=(ELASTICUSER,ELASTICPASS)
)

# Prueba para ver si hubo una conexion correcta
try:
    ESConnection.info()
except:
    raise Exception("Elastic no se conecto correctamente")

def borrar():
    ELASTICHOST = "http://localhost"#os.getenv("ELASTICHOST")
    ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
    ELASTICUSER = "elastic" #os.getenv("ELASTICUSER")
    ELASTICPASS = "m2Hl6qYVLMNFDfdZ" #cambiar contraseña si se desinstala #os.getenv("ELASTICPASS")

    # Create elasticsearch client
    ESConnection = Elasticsearch(
        ELASTICHOST+":"+ELASTICPORT,
        basic_auth=(ELASTICUSER,ELASTICPASS)
    )
    eliminarDoc = ESConnection.delete(index="groups", id= "job606-100")
    print(eliminarDoc)

def publicarElasticsearch():
    # Abrir archivo de ejemplo con la configuracion 
    archivo_local = os.path.join(os.path.dirname(__file__), 'ejemplo01.json')
    f = open(archivo_local,  "r")
    datos_archivo = f.read()

    response = ESConnection.index(
            index = "jobs",
            id = "job606",
            body = datos_archivo,
        )

    # Abrir archivo de ejemplo con la configuracion 
    archivo_local = os.path.join(os.path.dirname(__file__), 'documentoGrupo.json')
    f = open(archivo_local,  "r")
    datos_archivo = f.read()

    response = ESConnection.index(
            index = "groups",
            id = "job606-100",
            body = datos_archivo,
        )
    
    return 

def crearCola():
    """
    Prueba para crear una cola de rabbitmq
    """
    # Establecer conexion
    rabbitUserPass = pika.PlainCredentials("user","iX4rMustwltDPp7Y")
    rabbitConnectionParameters = pika.ConnectionParameters(
            host='localhost', 
            port='30100',
            credentials=rabbitUserPass
        )
    connection = pika.BlockingConnection(rabbitConnectionParameters)
    channel = connection.channel()

    QUEUE_NAME = 'ready' #cambiar luego

    # Crear cola
    channel.queue_declare(queue = QUEUE_NAME)

    print(" [x] Created Queue")

    connection.close()


def producir():
    """
    Publica un mensaje JSON en la cola creada anteriormente
    """
    rabbitUserPass = pika.PlainCredentials("user","iX4rMustwltDPp7Y")
    rabbitConnectionParameters = pika.ConnectionParameters(
            host='localhost', 
            port='30100',
            credentials=rabbitUserPass
        )
    connection = pika.BlockingConnection(rabbitConnectionParameters)
    channel = connection.channel()

    QUEUE_NAME = 'ready' #cambiar luego

    # Abrir archivo de ejemplo 
    archivo_local = os.path.join(os.path.dirname(__file__), 'msg.json')
    f = open(archivo_local,  "r")
    datos_archivo = f.read()

    while True:
        sleep(2) 
        # Publicar con un exchange a la cola
        channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=datos_archivo)

        print(" [x] Sent JSON message")

    connection.close()

def process(ch, method):
    ch.basic_ack(delivery_tag=method.delivery_tag, multiple=False)
    print("IM DONE")


def callback(ch, method, properties, body):
    print(" [x] Received = ", body)
    process(ch, method)


def consumirCola():
    """
    Prueba para recibir el mensaje JSON de la cola creada anteriormente
    """
    rabbitUserPass = pika.PlainCredentials("user","iX4rMustwltDPp7Y")
    rabbitConnectionParameters = pika.ConnectionParameters(
            host='localhost', 
            port='30100',
            credentials=rabbitUserPass
        )
    connection = pika.BlockingConnection(rabbitConnectionParameters)
    channel = connection.channel()

    QUEUE_NAME = 'ready' #cambiar luego

    channel.basic_consume(queue=QUEUE_NAME, auto_ack=False, on_message_callback=callback)

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

#borrar()
#publicarElasticsearch()
#crearCola()
producir()

# Se comento para poder probar la app como consumidor
#consumirCola()