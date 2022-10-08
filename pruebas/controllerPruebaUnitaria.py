"""
Controlador para prueba unitaria del elasticsearch publisher app
"""

import pika
import os

def crearCola():
    """
    Prueba para crear una cola de rabbitmq
    """
    # Establecer conexion
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    QUEUE_NAME = 'root.stages[name=load].source_queue'

    # Crear cola
    channel.queue_declare(queue = QUEUE_NAME)

    print(" [x] Created Queue")

    connection.close()


def producir():
    """
    Publica un mensaje JSON en la cola creada anteriormente
    """
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    QUEUE_NAME = 'root.stages[name=load].source_queue'

    # Abrir archivo de ejemplo 
    my_local_file = os.path.join(os.path.dirname(__file__), 'msg.json')
    f = open(my_local_file,  "r")
    my_local_data = f.read()

    # Publicar con un exchange a la cola
    channel.basic_publish(exchange='', routing_key=QUEUE_NAME, body=my_local_data)

    print(" [x] Sent JSON message")

    connection.close()

def consumirCola():
    """
    Prueba para recibir el mensaje JSON de la cola creada anteriormente
    """
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()

    QUEUE_NAME = 'root.stages[name=load].source_queue'

    def callback(ch, method, properties, body):
        print(" [x] Received = ", body)

    channel.basic_consume(queue=QUEUE_NAME, auto_ack=True, on_message_callback=callback)

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

crearCola()
producir()
consumirCola()