USE my_database;

CREATE TABLE persona (
cedula integer not null, 
nombre varchar (50), 
id integer auto_increment, 
provincia varchar(30), 
canton varchar(30),
primary key (id)
);

INSERT INTO persona (cedula, nombre,provincia,canton) VALUES (3000,'Daniela','san jose','curri');
INSERT INTO persona (cedula, nombre,provincia,canton) VALUES (4000,'Sonia','cartago','tres rios');
INSERT INTO persona (cedula, nombre,provincia,canton) VALUES (3526,'Antony','heredia','centro');
INSERT INTO persona (cedula, nombre,provincia,canton) VALUES (4789,'Yendry','heredia','centro');
INSERT INTO persona (cedula, nombre,provincia,canton) VALUES (5785,'Maria','san jose','pavas');
INSERT INTO persona (cedula, nombre,provincia,canton) VALUES (1230,'Carlos','cartago','centro');
INSERT INTO persona (cedula, nombre,provincia,canton) VALUES (1248,'Antonio','cartago','turrialba');
INSERT INTO persona (cedula, nombre,provincia,canton) VALUES (8964,'Eva','alajuela','centro');
INSERT INTO persona (cedula, nombre,provincia,canton) VALUES (9521,'Roxana','san jose','barrio amon');
INSERT INTO persona (cedula, nombre,provincia,canton) VALUES (15890,'Luisa','san jose','escazu');

SELECT * FROM persona;
