import unittest
from elasticsearch import Elasticsearch
import mariadb
import json

# Python code to demonstrate working of unittest
import unittest

from sqlalchemy import false

class TestStringMethods(unittest.TestCase):

    def setUp(self):
        pass
	
    def connectToMariaDB(self):
        connectionSucces = false
        try:
            conn = mariadb.connect(
            user="root",
            password="iy5PtSwCIo",
            host="127.0.0.1",
            port=32100,
            database="my_database")

            connectionSucces = True

        except mariadb.Error as e:
            connectionSucces = False
        
        self.assertTrue(connectionSucces)
    
    def holaMundo(self):
        self.assertEqual("HOLA", "HOLA")


if __name__ == '__main__':
    unittest.main()
