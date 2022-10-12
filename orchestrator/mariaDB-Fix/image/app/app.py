import mariadb

conn = mariadb.connect(
        user="root",
        password="FWUQsV078G",
        host="localhost",
        port=32150,
        database="my_database"
    )

statement = "CREATE TABLE pais(id_pais INT AUTO_INCREMENT,nombre VARCHAR(20),PRIMARY KEY (id_pais))"
statement1 = "SHOW TABLES"
cursor = conn.cursor()
#cursor.execute(statement)
cursor.execute(statement1)
conn.commit()

for table in cursor:
    print(table)