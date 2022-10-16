import mariadb
import string
import random
from names_dataset import NameDataset
from pandas import *
from random import randint
import sys
import os


# Global variables
length = 1000
plates = []
cars = []
nombresList = []
cedulas = []
ids = []
peopleData = []
carData = []
provincias = ["Alajuela", "Cartago", "San Jose", "Heredia", "Limon", "Puntarenas", "Guanacaste"]
names = NameDataset()

"""
generate_plates: algorithm that generates random car plates
Original code was taken in: https://www.geeksforgeeks.org/python-generate-random-string-of-given-length/

"""

def generate_plates(quantity,large):
    number_of_strings = quantity
    length_of_string = large

    for x in range(number_of_strings):
        letras = ''.join(random.SystemRandom().choice(string.ascii_letters) for _ in range(length_of_string))
        numeros = ''.join(random.SystemRandom().choice(string.digits) for _ in range(length_of_string))
        plates.append(letras + "-" + numeros)

"""
Read the CSV file columns and merge them into just one field and added to global variable cars 
"""
def generateDescription():
    # reading CSV file
    data = read_csv(os.path.join(os.path.dirname(__file__), "USA_cars_datasets.csv"))
 

    br = data['brand'].tolist()
    md = data['model'].tolist()
    ye = data['year'].tolist()
    co = data['color'].tolist()


    generate_plates(length,3)

    for i in range(length):
        car = [br[i] + " " + md[i] + " " + plates[i] + " " + str(ye[i]) + " " + co[i]]
        cars.append(car)

#Generate a random cedula and add it to cedulas global variable
def cedulaRandom():
    for i in range(length):
        cedulas.append(str(randint(1,9)) + "-" + str(randint(1000,9999)) + "-" + str(randint(1000,9999)))

# Takes random names from NameDataset and create random names
def generatePeople():
    nombresDict = names.get_top_names(n=length,country_alpha2='CR')
    apellidosDict = names.get_top_names(n=length,country_alpha2='CR',use_first_names=False)

    nombres = nombresDict['CR']['M'] + nombresDict['CR']['F']
    apellidos = apellidosDict['CR']

    for i in range(length):
        nombresList.append(nombres[i] + " " + apellidos[i])

# Generate random ids
def generateIDs():
    for i in range(length):
        ids.append(str(randint(0,length)))

# Generate people data, it first create cedulas, sencond create different names and finally create random ids, after that merge it into just one value
def generatePeopleData():
    cedulaRandom()
    generatePeople()
    generateIDs()
    for i in range(length):
        peopleData.append([cedulas[i],nombresList[i],ids[i],provincias[randint(0,6)]])

#Generate different cars information named as Description
def generateCarData():
    generateDescription()
    for i in range(length):
        carData.append([randint(0,length), peopleData[i][2], cars[i][0]])

#Main function, connect to database and add random dataset to car and persona
def dataset():
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
        sys.exit(1)

    
    # Get Cursor
    cur = conn.cursor()

    #Delete tables before create new ones again
    cur.execute("DROP TABLE IF EXISTS car")
    cur.execute("DROP TABLE IF EXISTS persona")
    

    #Create new tables persona & car
    cur.execute(
        """CREATE TABLE IF NOT EXISTS persona(
	cedula varchar(15),
    nombre varchar(50) not null,
    id int primary key auto_increment,
    provincia varchar(10))""")

    cur.execute("""CREATE TABLE IF NOT EXISTS car(
        id int, owner int not null, description varchar(100) not null,
        foreign key (owner) references persona(id))""")

    #Generate DATASET
    generatePeopleData()
    generateCarData()

    #Add people to table persona
    for i in range(length):
        cedula = peopleData[i][0]
        nombre = peopleData[i][1]
        id = peopleData[i][2]
        provincia = peopleData[i][3]
        cur.execute("INSERT INTO persona(cedula,nombre,provincia) VALUES (" + "'" + cedula + "'" + ", " + "'" + nombre + "'" + ", " + "'" +provincia + "'" + ")")
    
    #Commiting updates
    conn.commit()

    #Add car to table car
    for i in range(length):
        cur.execute("INSERT INTO car(id,owner,description) VALUES (" + "'" + str(carData[i][0]) + "'" + ", " + "'" + str(i+1) + "'" + ", " + "'" +carData[i][2] + "'" + ")")

    #Commiting updates
    conn.commit()

    #Get info to verify
    cur.execute("SELECT * FROM persona")
    for i in cur:
        print(i)


    cur.execute("SELECT * FROM car")
    for i in cur:
        print(i)


    #Close connection
    conn.close()



if __name__ == '__main__':
    dataset()

