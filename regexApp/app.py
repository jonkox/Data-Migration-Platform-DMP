import re

import json

with open("ejemplo01.json") as archivo:
    datos = json.load(archivo)

print(datos["job_id"])



print(re.search("[a-z1-9]",datos["job_id"]))

