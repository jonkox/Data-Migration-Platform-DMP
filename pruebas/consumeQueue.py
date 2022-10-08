"""
Prueba para recibir el mensaje JSON de la cola creada anteriormente
"""

import pika

connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
channel = connection.channel()

QUEUE_NAME = 'root.stages[name=load].source_queue'

def callback(ch, method, properties, body):
    print("Received = ", body)

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