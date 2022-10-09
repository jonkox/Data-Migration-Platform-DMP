from time import sleep
from elasticsearch import Elasticsearch
import random

ELASTICHOST = "localhost"#os.getenv("ELASTICHOST")
ELASTICPORT = "32500"#os.getenv("ELASTICPORT")
ELASTICPASS = "" #os.getenv("ELASTICPASS")

elasticClient = Elasticsearch("http://"+ELASTICHOST+":"+ELASTICPORT)

elasticClient.indices.delete(index="jobs")
elasticClient.indices.delete(index="groups")

if(not (elasticClient.indices.exists(index=["jobs"]))):
    elasticClient.indices.create(index="jobs")

doc = {
    "job_id" : "nuevojob",
    "status": "new",
    "msg": "",
    "data_sources": [
        {
            "type": "elasticsearch",
            "name": "destination_es",
            "url": "http://localhost",
            "port": "32500",
            "usuario": "",
            "password": ""
        },
        {
            "type" : "mysql",
            "name": "people_db",
            "url": "localhost",
            "port": "32150",
            "usuario": "root",
            "password": "ceryur1E8f"
        }
    ],
    "control_data_source": "destination_es",
    "source": {
        "data_source": "people_db",
        "expression": "SELECT * FROM persona ORDER BY cedula",
        "grp_size": "100"
    }
}

string = "nuevojob"

for i in range(0,1):
    doc["job_id"] = "nuevojob" + str(random.randint(0,1000))
    elasticClient.index(index="jobs", document=doc)