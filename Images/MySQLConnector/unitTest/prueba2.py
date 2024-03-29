import json
from turtle import clear
from elasticsearch import Elasticsearch
import urllib3
urllib3.disable_warnings()

#Para conectar el puerto de Elasticsearch, ponerlo en consola y asegurar que elastic se este ejecutando--
#kubectl port-forward quickstart-es-default-0 9200:9200

# Password for the 'elastic' user generated by Elasticsearch
ELASTIC_PASSWORD = "4949QwH1tyM37hL8owoD3e2p"

# Create the client instance
es = Elasticsearch(['https://localhost:9200'],basic_auth=('elastic',ELASTIC_PASSWORD),verify_certs=False)

#Leer un json y ver el contenido que queremos

#Crea el indice jobs y le annade el json de ejemplo con id 1
def cargarElastic():
    with open("ejemplo01.json") as prueba:
        contenido = json.load(prueba)
        result = es.create(index="jobs",id=1,body=contenido)
        print("-----------------------------------")
        print(result)
        print("-----------------------------------")

#Carga el Json publicado en elastic y lo lee
def cargarJson():
    resp = es.get(index="jobs", id=1) #carga
    print("-----------------------------------")
    contenido = resp['_source'] #Josn con el id 1 del indice jobs
    for i in contenido:
        if i == "data_sources":
            for j in contenido[i]:
                contenido2 = j
                print(contenido2) #Imprime la fila                   
                for k in contenido2: #Entra a la lista
                    #Imprime "Type -- mysql"o name -- people
                    ##k es la llave y contenido2[k]es el valor
                    print(k+"--"+contenido2[k])                      
                return
    print("-----------------------------------")
    
if __name__ == '__main__':
    #cargarElastic()
    cargarJson()
