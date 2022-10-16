import mariadb
from tabulate import tabulate
#Connect to mariadb
try:
    conn = mariadb.connect(
        user="root",
        password="IteAgY6fBV",
        host="127.0.0.1",
        port=32100,
        database="my_database")

    print("Connection succesfully")
except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")

cur = conn.cursor()

print("\n--------------------TABLA PERSONAS-----------------------")
cur.execute("SELECT * FROM persona LIMIT 20")
print(tabulate(cur.fetchall(),headers=['Cedula','Nombre','ID','Provincia']))
cur.execute("SELECT count(1) FROM persona")
print("Cantidad de registros: " + str(cur.fetchone()[0]))

print("\n---------------------TABLA CARROS------------------------")
cur.execute("SELECT * FROM car LIMIT 20")
print(tabulate(cur.fetchall(),headers=['ID','Dueño','Descripcion']))
cur.execute("SELECT count(1) FROM car")
print("Cantidad de registros: " + str(cur.fetchone()[0]))
