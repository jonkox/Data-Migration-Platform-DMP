import elasticsearch

from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200/'], verify_certs=True)

if not es.ping():
    raise ValueError("Connection failed")