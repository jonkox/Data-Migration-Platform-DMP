from ast import Delete
from elasticsearch import Elasticsearch,NotFoundError
import DATASET
import json
import os

# Elastic
ELASTICHOST = "localhost"
ELASTICPORT = "32500"
ELASTICUSER = "elastic"
ELASTICPASS = "vLjjh9ojWfyn4FNq" 

# MariaDB
DATASET.MARIADBNAME = "my_database"
DATASET.MARIADBHOST = "localhost"
DATASET.MARIADBPORT = 32100
DATASET.MARIADBUSER = "root"
DATASET.MARIADBPASS = "VFZs3RpO1X"

# RabbitMQ
RABBITHOST = "localhost" 
RABBITPORT = "30100" 
RABBITUSER = "user" 
RABBITPASS = "64iBHzjtzmxs2ZPv"
RABBITQUEUENAME = "orchestrator"

elasticClient = Elasticsearch("http://"+ELASTICHOST+":"+ELASTICPORT, basic_auth=(ELASTICUSER,ELASTICPASS))
try:
    elasticClient.info()
except Exception as e:
    raise("Error occured during elasticsearch connection: " + e)

def purgeCustomIndex():
    while True:
        index = input("Index Name to purge: ")
        try:
            elasticClient.indices.delete(index=index)
            print("Index '" + index + "' deleted successfully")
            break
        except NotFoundError:
            print("Index doesn't exist, try again\n")

def injectCustomJSON():
    while True:
        jsonName = input("JSON Name to inject: ")
        try:
            with open(os.path.join(os.path.dirname(__file__),jsonName)) as archivo:
                jsonFile = json.load(archivo)
            elasticClient.index(index="jobs", document=jsonFile)
            print("Job injected successfully")
            break
        except NotFoundError:
            print("File doesn't exist, try again\n")


def getNumber(message):
    result = None
    failed = True
    while failed:
        option = input(message)
        try:
            result = int(option)
        except ValueError:
            message = "Try again: "
            continue
        return result

with open(os.path.join(os.path.dirname(__file__),"job0.json")) as archivo:
    job0 = json.load(archivo)

with open(os.path.join(os.path.dirname(__file__),"job1.json")) as archivo:
    job1 = json.load(archivo)

def purgeJobsAndGroups():
    if((elasticClient.indices.exists(index=["jobs"]))):
        elasticClient.indices.delete(index="jobs")
    if((elasticClient.indices.exists(index=["groups"]))):
        elasticClient.indices.delete(index="groups")
    elasticClient.indices.create(index="jobs")
    elasticClient.indices.create(index="groups")
    print("Purge Successfully")

while True:

    print("\n0. Inject Job0 in Elastic")
    print("1. Inject Job1 in Elastic")
    print("2. Inject Custom Job in Elastic")
    print("3. Load Data To MariaDB")
    print("4. Purge elastic jobs and groups index")
    print("5. Purge custom index")
    print("6. Exit")
    option = getNumber("Select an option: ")

    if( not (0 <= option and option <= 6) ):
        print("\nOption not available")
        continue
    if(option == 0):
        electedJob = job0
    elif(option == 1):
        electedJob = job1
    elif(option == 2):
        injectCustomJSON()
        continue
    elif(option == 3):
        DATASET.dataset()
        continue
    elif(option == 4):
        purgeJobsAndGroups()
        continue
    elif(option == 5):
        purgeCustomIndex()
        continue
    else:
        break

    elasticClient.index(index="jobs", document=electedJob)
    print("Job injected, you can choose again")


