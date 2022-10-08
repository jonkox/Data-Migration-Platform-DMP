import elasticsearch
from elasticsearch import Elasticsearch

# Crea la instancia de un cliente
es = Elasticsearch('http://localhost:32500')

print(es.info())