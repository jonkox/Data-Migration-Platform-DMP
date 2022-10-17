import pika
import os

# RabbitMQ
RABBITHOST = os.getenv("RABBITHOST")
RABBITPORT = os.getenv("RABBITPORT")
RABBITUSER = os.getenv("RABBITUSER")
RABBITPASS = os.getenv("RABBITPASS")
RABBITQUEUEMYSQL = os.getenv("RABBITQUEUEMySQL") #Cola que debo enviar

class bcolors:
    OK      = '\033[92m'    #GREEN
    RESET   = '\033[0m'     #RESET COLOR

#Lo que hago con el mensaje de entrada
def callback(ch, method, properties, body):
    #print("mensaje de mysql: ", body)
    print(f"{bcolors.OK} Mensaje que recibe de MySQL Connector: {bcolors.RESET}", body)
    return

credentials_ = pika.PlainCredentials(RABBITUSER, RABBITPASS)
parameters = pika.ConnectionParameters(host=RABBITHOST, port=RABBITPORT, credentials=credentials_)
connection = pika.BlockingConnection(parameters)
channelConsuming = connection.channel()
channelConsuming.queue_declare(queue=RABBITQUEUEMYSQL)
channelConsuming.basic_consume(queue=RABBITQUEUEMYSQL, on_message_callback=callback, auto_ack=True)
#print('Waiting for messages.')
channelConsuming.start_consuming()
