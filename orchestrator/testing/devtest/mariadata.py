import mariadb
from names_dataset import *
from random import randint

conn = mariadb.connect(
        user="root",
        password="ceryur1E8f",
        host="localhost",
        port=32100,
        database="my_database"
    )
mariaCursor = conn.cursor()
names = NameDataset()

def cedulaRandom():
    return str(randint(1,9)) + "-" + str(randint(1000,9999)) + "-" + str(randint(1000,9999))

def getAllFromPersona():
    mariaCursor.execute("SELECT * FROM persona")
    for i in mariaCursor:
        print(i)

tableCreation = "CREATE TABLE persona \
    ( \
    id_persona INT AUTO_INCREMENT, \
    nombre VARCHAR(60), \
    cedula VARCHAR(11), \
    PRIMARY KEY (id_persona) \
    )"

mariaCursor.execute("SHOW TABLES LIKE 'persona'")

if(mariaCursor.fetchone() == None):
    mariaCursor.execute(tableCreation)

nombresDict = names.get_top_names(n=500,country_alpha2='CR')
apellidosDict = names.get_top_names(n=500,country_alpha2='CR',use_first_names=False)

nombres = nombresDict['CR']['M'] + nombresDict['CR']['F']
apellidos = apellidosDict['CR']

mariaCursor.execute("SELECT Count(1) FROM persona")
if(mariaCursor.fetchone()[0] <= 0):
    for i in range(0,23):
        for j in range(0,23):
            nombre = nombres[i] + " " + apellidos[j]
            cedula = cedulaRandom()
            mariaCursor.execute("INSERT INTO persona (nombre,cedula) VALUES (" + "'" + nombre + "'" + ", " + "'" + cedula + "'" + ")")
    conn.commit()

