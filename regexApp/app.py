import re
from unittest import result
import mariadb
from elasticsearch import Elasticsearch
import json
from datetime import datetime

with open("regexApp/ejemplo01.json") as archivo:
    datos = json.load(archivo)
    expression = datos["stages"][1]["transformation"][1]["regex_config"]["regex_expression"]

op = False


if op == True:

    es = Elasticsearch("http://localhost:9200")

    es.index(index='lord-of-the-rings',document={
    'character': 'Frodo Baggins',
    'quote': 'You are late'
    })


#-------------------------------------------------------------------------------------------


if op == False:
    try:
        conn = mariadb.connect(
            user="root",
            password="JC8OQiUXbG",
            host="127.0.0.1",
            port=32100,
            database="my_database"

        )
        print("Connection succesfully")

    except mariadb.Error as e:
        print(f"Error connecting to MariaDB Platform: {e}")
        sys.exit(1)

    # Get Cursor
    cur = conn.cursor()

    cur.execute(
        "SELECT description FROM car")

    for i in cur:
        match = re.findall(expression,i[0])
        if match:
            print(match[0])

    conn.close()