# Data-Migration-Platform-DMP

# Proyecto Data Migrations Platform
    Instituto Tecnológico de Costa Rica
    Escuela de Ingeniería en Computación 
    IC-4302 Bases de Datos II
    Prof. Nereo Campos
    IIS 2022

## Integrantes

    Johnny Díaz Coto         - 2020042119
    Andrea Li Hernández      - 2021028783
    Deyan Sanabria Fallas    - 2021046131
    Pamela González López    - 2019390545

## Instrucciones de como ejecutar el proyecto
El proyecto se encuentra en un repositorio privado de GitHub, el profesor del curso o las personas permitidas pueden realizar la instalación sin ningún problema, en el caso de personas fuera del repositorio, en caso de cambiarse la configuración de este también podrían hacer las mismas cosas que se explicaran a continuación.

### Clonación del Repositorio
Para poder clonar los documentos que se encuentran en GitHub se debe realizar el siguiente comando:

```bash
git clone https://github.com/jonkox/Data-Migration-Platform-DMP.git
```
Esto lo que hará es descargar el proyecto dentro de la computadora que lo ejecute. Es recomendable tener una cuenta de GitHub para evitar algunos problemas con la autenticación.
Hecho este paso debe obtener el proyecto con una distribución así:
<div style="text-align: center;"><img src=https://i.imgur.com/eJ6EifJ.png
></div>

El proyecto se constituye de varias carpetas, cada una de ellas tiene su función, sin embargo se pueden dividir en dos grupos, estos son:
* Helm Charts
    * application
    * databases
    * monitoring
* Aplicaciones
    * Images
        * ElasticSearchPublisher
        * MySQLConnector
        * Orchestrator
        * REGEXProcessor
        * SQLProcessor
    * Pruebas

Las aplicaciones contienen todo el código necesario para ejecutar la tarea que cada una de ellas debe de cumplir, estas se dividen en el código de producción y la rama de pruebas.
Por otro lado, los Helm Charts son utilizados para instalar todas las herramientas dentro de Kubernetes, donde cada Helm Chart instala distintas herramientas de la siguiente manera:

* application
    * Instala todas las aplicaciones creadas por el equipo de trabajo.
* databases
    * Instala las bases de datos que se necesitan en el proyecto, ElasticSearch y MariaDB.
* monitoring
    * Instala todas las herramientas de monitoreo del proyecto: prometheus, grafana y rabbitmq.

### Pasos de Instalación
1. Posicionarse en la carpeta principal del proyecto.
2. Ejecutar el comando:
```bash!
helm install [name][chart]
```
En nuestro caso serían los siguientes comandos:
```bash!
helm install databases databases
helm install monitoring monitoring
helm install application application
```
### Nota
Al crear un Helm Chart e instalarlo, se va a utilizar el nombre del chart seguido por el nombre del componente en cuestión, *[nombre del chart]-[nombre del componente]*. En nuestro caso por ejemplo, con el Helm Chart encargado del monitoreo tiene como nombre “monitoring”, así que un ejemplo práctico del nombre de un pod es **monitoring-mariadb**, dónde esto lo podemos saber con anticipación gracias al nombre del chart y el componente que se desea instalar.
Ahora, esto nos afecta directamente en distintas situaciones, dónde continuando con el ejemplo de monitoring:
* En el momento de obtener la contraseña de MariaDB por medio de variables de entorno se tiene la siguiente sección dentro del deployment:
```yaml
- name: "MARIADBPASS"
  valueFrom:
  secretKeyRef:
    name: databases-mariadb
    key: mariadb-root-password
    optional: false
```
Al momento de escribir el código necesario para esta tarea se tiene en cuenta los nombres de los componente para así conocer desde antes su valor, por tanto, es importante tener en cuenta el nombre de los charts al momento de su creación y programación a sus al rededores.

## Explicación de Secciones Varias

### Values de Application
El archivo values.yaml que se puede encontrar en la carpeta ./application contiene la información que necesitan componentes como ElasticSearch, RabbitMQ, MariaDB. Para estos se tienen valores **generales** que debe utilizar cada aplicación del sistema, estas son:

    Host: Dirección del proveedor.
    Port: Puerto de conexión.
    User: Usuario con el cual brinda el acceso al servicio.
    
Lo que podemos encontrar dentro del archivo es:
```yaml
general:
  # Elastic
  elastichost: "http://databases-elasticsearch-master-hl.default.svc.cluster.local"
  elasticport: "\"9200\""
  elasticuser: "elastic"

  # RabbitMQ
  rabbithost: "monitoring-rabbitmq-headless"
  rabbitport: "\"5672\""
  rabbituser: "user"

  # Mariadb
  mariadbname: "my_database"
  mariadbhost: "databases-mariadb-primary"
  mariadbport: "\"3306\""
  mariadbuser: "root"
```

Ahora, con los componentes creados por el equipo se tienen valores para cada uno de ellos, estos consisten en: cantidad de réplicas y nombre de la cola de RabbitMQ en caso de ser necesario. Un ejemplo práctico sería el siguiente caso:

```yaml
sqlprocessor:
  replicas: 1
  rabbitqueuename: "sqlprocessor"
```
Al final este archivo nos ayuda en la configuración de cada uno de los componentes y especificar la cantidad de réplicas que se desean de cierto componente.



### NodePorts
Los servicios de tipo NodePort nos permiten comunicar componentes dentro del cluster de Kubernetes con los componentes fuera de este ambiente, esto es muy funcional para poder visualizar distintos puntos desde aplicaciones terceras o tener la seguridad de un host y port donde vamos a poder consultar por datos.
Para poder crear un servicio de tipo NodePort se tienen dos opciones, crear un servicio mediante un archivo yaml o mediante la configuración en el values dentro del Helm chart correspondiente. En nuestro grupo de trabajo se escogió la segunda opción.

Esto se ve de la siguiente manera dentro del values del Helm Chart databases:

```yaml!
kibana:
  service:
    type: NodePort
    nodePorts:
      http: 31500
```
Este es un ejemplo de los varios que hay dentro del documento, en este caso, Kibana. Para poder crear este servicio se necesita:
* Especificar el servicio.
* Especificar el tipo de servicio, en este caso NodePort.
* Especificar el puerto a exponer, en este caso fue el 31500. Los puertos deben estar dentro de un rango de **[30000,32767]**.

Dentro del proyecto todos los componentes de monitoring y databases tienen sus propios NodePorts para un mejor manejo durante la etapa de desarrollo, sin embargo, si el usuario desea seguir con el clásico ClusterIP se debe cambiar simplemente el tipo de servicio.

    type: NodePort  --> type: ClusterIP



### Recursos
Limitación de recursos, la elaboración del proyecto fue un poco difícil ya que todos los integrantes no poseen la facilidad de un equipo con los recursos suficientes para poder levantar todos los componentes que se necesitaban dentro del proyecto, es por eso que se optó por ciertas opciones que ayudaban a reducir el consumo de memoria, una de las soluciones para este tipo de situaciones es la limitación de los componentes, en términos generales esto consiste en darle valores máximos de uso de los recursos a cada una de las aplicaciones que se encuentran corriendo, lo que nos ayuda a la reducción general del uso de memoria.

Para cada componente que se quiera limitar se sigue una plantilla general:


```yaml
resources:
  limits: 
    cpu: 100m
    memory: 128Mi
  requests:
    cpu: 100m
    memory: 128Mi
```
Donde los valores ingresados son medidos por:
* m  --> milésima de núcleo (thousandth of a core)
* Mi --> Mibibyte

De esta menera se puede ir por cada componente hasta llegar un balance del consumo de recursos en de uso y de request para un mejor rendimiento.

---
## Contraseñas
Los componentes de ElasticSearch, MariaDB y RabbitMQ poseen sus contraseñas, en nuestro equipo de trabajo no se vio necesaria la estipulación de contraseñas definidas, sino que, por el contrario, cada uno de los componentes genera su propio usuario y contraseña. A raíz de esta situación es que antes de realizar alguna de las pruebas que se documentan en esta sección debe tener presente esto.
Al momento de instalar los componentes debe recuperar las contraseñas e insertarlas en los espacios correspondientes, para esto se deben seguir los siguientes pasos:
* Utilizar la aplicación Lens para una mejor comodidad.
* Navegar a la conexión del cluster, en la sección "Config" se encuentra un espacio de nombre "Secrets".
<div style="text-align: center;"><img src=https://i.imgur.com/m21RV98.png></div>
* Una vez en esta sección se pueden ver todos los secrets de todos los componentes, así que de esta menera podemos seleccionar el componente en cuestión, obtener sus información de acceso y sustituirlo en los archivos de prueba que se mencionan en las secciones siguientes.

Para continuar con el ejemplo, se obtendrá la contraseña de ElasticSearch, esta se puede encontrar seleccionando el componente en la sección de secrets vista, por lo que se obtiene lo siguiente:
<div style="text-align: center;"><img src=https://i.imgur.com/PyrtXYq.png></div>

La contraseña encontrada se escribirá dentro del espacio correspondiende en el archivo de pruebas como se ve a continuación:
<div style="text-align: center;"><img src=https://i.imgur.com/FlsPkHK.png></div>

Note la línea azul de la izquierda, en ese punto es dónde se ha inscrito la contraseña.

Debe tener esto en cuenta antes de replicar cada una de las pruebas que en este documento se detallan.

### NOTA
Al momento de realizar la instalación de cada uno de los componentes crea un *Persistant Volume Claim* (PVC) y un *Persistant Volume* (PV) dónde se guarda la información que contienen en ese momento de manera persistente, al momento de desinstalar los componentes estas secciones no se eliminan, es por eso que si al reinstalar los componentes y realizar los pasos anteriores no funcionan, asegúrese de haber eliminado previamente los PVC y PV antes de volver a instalar los componentes, pues la información de la contraseña que se está mostrando no es la correcta, ya que se muestra la contraseña actual, pero los componentes están tomando como contraseña la que dice el PVC y el PV, que son de instalaciones previas.
Con la ayuda de Lens es muy fácil realizar este proceso con los siguientes pasos:
* En la sección de Storage, seleccionar el espacio de PVC.
* Seleccionar los elementos a eliminar.
* Eliminarlos.

<div style="text-align: center;"><img src=https://i.imgur.com/JJ2q8P2.png></div>







## Pruebas realizadas

## Pruebas Generales

Para la ejecución de las pruebas generales se necesita tener todos los componentes previamente instalados.
Con el comando
```bash
kubectl get pods
```
Si los pasos de instalación fueron ejecutados correctamente se debe obtener el siguiente resultado:
<div style="text-align: center;"><img src=https://i.imgur.com/21RHUCa.png
></div>

Esto indica que se tienen todos los componentes del proyecto instalados de buena manera y funcionando.

Una vez con todos los componentes instalados de buena menera, se procede con la prueba general de funcionamiento:

### Programa de Inserción de Datos
Como se puede ver, al momento de la clonación del proyecto, este contiene una capeta de nombre "Pruebas" la cual contiene distintos archivos que han funcionado para la inserción de distintos datos de prueba, en este caso el archivo *jobInjection*.py es el encargado de todas estas inserciones. Al momento de ejecutar dicho archivo se optiene el siguiente menú:
<div style="text-align: center;"><img src=https://i.imgur.com/t6BGvZq.png
></div>

**Recuerde** que antes de la ejecución del programa ambas bases de datos se encuentran vacías.

El orden de ejecución puede variar dependiendo del caso y de la persona que este ejecutando el programa, en este ejemplo se segurá el siguiente camino:
* Seleccionar la opción 3 "**Load Data To MariaDB**"
Esto inserta datos de prueba a MariaDB para ser tomados en cuenta en procesos posteriores. 
Momentos antes de realizar este proceso:
<div style="text-align: center;"><img src=https://i.imgur.com/FyO0gIy.png></div>

Después de la inserción:
<div style="text-align: center;"><img src=https://i.imgur.com/CLrlrVm.png></div>

---

* Seleccionar la opción 0 "**Inject Job0 in Elastic**"


**Momentos antes** de realizar este proceso y siguiendo la consulta
```json
GET _search
{
  "query": {
    "match" : {"_index":"jobs"}
  }
}
```
Se obtiene como resultado:
<div style="text-align: center;"><img src=https://i.imgur.com/OuphbKg.png></div>

**Después** de la inserción y ejecutando la misma consulta:
<div style="text-align: center;"><img src=https://i.imgur.com/oRM3d8f.png></div>

Note que el campo "value" contiene un valor de 1, que indica la cantidad de documentos que contiene el índice, pues solo se ha ingresado 1 job con el programa.

A partir de este punto es un poco difícil poder ejemplificar cada paso con imágenes, pues todo sucede de manera muy rápida como para poder tomar captura del momento exacto. Es por eso por lo que para un ejemplo más visible se ha tomado un video con el proceso a partir de este punto. Para este video se ejecuta el a partir del momento en que se ingresa el job con el programa de inserción de datos, se comprueba que no haya nada dentro de ElasticSearch hasta ese punto, luego de ello se pueden ver los logs de cada uno de los componentes del programa y finalmente se ven los resultados finales que se han generado en el nuevo índice gracias al componente de ElasticSearch Publisher.
El video se puede encontrar en [YouTube](https://youtu.be/6z5NTNctt4Y).

Finalmente se obtienen los resultado de la tranformación realizada en el proceso de migración, para esto se debe consultar el índice "personas" que ha creado el componente ElasticSearch Publisher, dónde se obtiene un resultado de:
<div style="text-align: center;"><img src=https://i.imgur.com/5MKvIXB.png></div>

Para comprobar este resultado se puede ejecutar la siguiente consulta en MariaDB:

```sql
SELECT p.cedula, p.nombre, p.id, p.provincia, c.description
FROM persona as p
JOIN
car as c 
ON c.owner = p.id
WHERE p.id = 281;
```
Con la consulta se puede obtener la información base que se tomó para la transformación. Note que el valor 281 se refiere al "id" de la persona.

<div style="text-align: center;"><img src=https://i.imgur.com/uxmIMzn.png></div>

Finalmente, con toda esta información se puede ver el funcionamiento general del programa. Recuerde que la prueba vista ha sido algo general que ha sido utilizada para ejemplificar el buen funcionamiento del programa, sin embargo está plenamente abierto a cambios que puedan surgir en distintos casos de prueba, si cambia cualquier set de datos puede obtener resultados distintos siguiendo las reglas de lo que el programa necesita como insumos para iniciar su trabajo.

---

## Resultados de las pruebas unitarias.
### Prueba unitaria del Orchestrator
El orchestrator es el componente inicial del sistema completo, previo a la etapa de Extract de un pipeline ETL. El orchestrator se encarga de dividir los registros de la base de datos en subgrupos especificados por un ‘Job’ entrante. Las siguiente dos pruebas buscan verificar que este proceso se haga de forma correcta. Ambas pruebas se hacen sobre una tabla con 1000 registros. Las pruebas vienen del archivo: *unitTestOrchestrator*.py acompañadas con una extra.

#### Primera Prueba
Se introduce el siguiente Job a elasticsearch (se muestra la parte que usa el orchestrator, puesto que el resto no es realmente relevante):
```json
{
    "job_id": "job0",
    "status": "new",
    "msg": "",
    "data_sources": [
        {
            "type": "mysql",
            "name": "mariadb",
            "url": "databases-mariadb-primary",
            "port": "3306",
            "usuario": "root",
            "password": "IteAgY6fBV"
        },
        {
            "type": "elasticsearch",
            "name": "destination_es",
            "url": "http://databases-elasticsearch-master-hl.default.svc.cluster.local",
            "port": "9200",
            "usuario": "elastic",
            "password": "5WKt5ymymHVmJsxQ"
        }
    ],
    "control_data_source": "destination_es",
    "source": {
        "data_source": "mariadb",
        "expression": "SELECT * FROM persona ORDER BY cedula",
        "grp_size": "100"
    }
}
```
##### Resultados:
La cola de publicación recibe lo siguiente:

<div style="text-align: center;"><img src=https://i.imgur.com/JkWeSxA.png></div>


Se publica lo siguiente en el índice Groups de Elastic:
    
<div style="text-align: center;"><img src=https://i.imgur.com/eFfewth.png></div>

Se modifica el status del Job en el índice Jobs:

<div style="text-align: center;"><img src="https://i.imgur.com/js0dzRe.png"></div>

Logs del componente:
<div style="text-align: center;"><img src="https://i.imgur.com/Rgi0mPh.png"></div>

#### Segunda Prueba:
Se introduce el siguiente Job a elasticsearch (se muestra la parte que usa el orchestrator, puesto que el resto no es realmente relevante):
```json
{
    "job_id": "job1",
    "status": "new",
    "msg": "",
    "data_sources": [
        {
            "type": "mysql",
            "name": "mariadb",
            "url": "databases-mariadb-primary",
            "port": "3306",
            "usuario": "root",
            "password": "IteAgY6fBV"
        },
        {
            "type": "elasticsearch",
            "name": "destination_es",
            "url": "http://databases-elasticsearch-master-hl.default.svc.cluster.local",
            "port": "9200",
            "usuario": "elastic",
            "password": "5WKt5ymymHVmJsxQ"
        }
    ],
    "control_data_source": "destination_es",
    "source": {
        "data_source": "mariadb",
        "expression": "SELECT * FROM persona ORDER BY cedula",
        "grp_size": "10"
    }
}

```
##### Resultados:
La cola de publicación recibe lo siguiente (se ponen los primeros y los ultimos porque son 100 mensajes):

<div style="text-align: center;"><img src=https://i.imgur.com/CxWWCN8.jpg></div>

Se publica lo siguiente en el índice Groups de Elastic (se ponen los primeros y los ultimos porque son 100 mensajes):

<div style="text-align: center;"><img src=https://i.imgur.com/Xtmy3c3.png></div>

Se modifica el status del Job en el índice Jobs:

<div style="text-align: center;"><img src=https://i.imgur.com/zeZ2g9I.png></div>

Logs del componente (se ponen los primeros y los ultimos porque son 100 mensajes):
<div style="text-align: center;"><img src=https://i.imgur.com/u15rx8x.png></div>

---

### Prueba unitaria de MySQL Connectors  

MySQL Connector es el encargado de actualizar un group especifico en Elasticsearch, añadirle un fiel ¨docs¨ el cual contendrá el resultado de una consulta que se realizará a MariaDB, esta consulta estará dada por un Json enviado a Elasticsearch. Como dato, para realizar esta prueba no es necesario tener ninguno de los otros componentes del proyecto funcionando solamente se necesita el helm chart de la prueba y los helm charts databases y monitoring.

Este componente debe realizar:  

* Consumir de una cola RabbitMQ. El mensaje que se consume tiene un job_id especifico para encontrar el json en el indice Job y un group_id para encontrar el group especifico a actualizar.
* Debe leer el json enviado a Elasticsearch para obtener la consulta que se realizará a MariaDB. 
* Actualizar el group indicado en el mensaje, añadiendole el fiel ¨docs¨ y dentro de este el resultado de la consulta realizada.
* Por último, debe enviar un mensaje a la una segunda cola RabbitMQ, indicando el job_id y el group_id.  

Para realizar la prueba se debe entrar a la carpeta Images/MySQLConnector/unitTest la cual contiene lo siguiente:  

* Maria.sql: Esto es para que se cree la base de datos pequeña para la prueba.
* ejemplo02.json: El json que se debe subir al indice jobs en Elasticsearch.
* ImagenesParaPrueba: Estas imagenes son las que se hicieron para ejecutar la prueba.
* application-demo: Este es el helm chart que se debe ejecutar para realizar la prueba.  

#### Pasos y resultados para reproducir la prueba  
1- Se debe conectar MariaDB en MySQL Workbench y ejecutar el archivo Maria.sql. Cuando se ejecute, se debe tener una tabla persona con lo siguiente:

<div style=“text-align: center;”><img src=https://i.imgur.com/vvGJIWz.png></div> 

2- Se debe tener en Elasticsearch un indice llamado ¨jobs¨ y añadirle el ejemplo02.json adjunto a en la carpeta. Luego se debe ejecutar el helm chart application-demo. Este helm levanta 3 pods los cuales el primero se llama **produce** que envía un mensaje a la primera cola que indica el job_id y el group_id que se debe actualizar,además se añade dicho group a Elasticsearch.  

**Mensaje que envía a la primera cola:**  


<div style=“text-align: center;”><img src=https://i.imgur.com/Hpjonen.png></div>   


**Como se ve el group en Elasticsearch antes de que MySQL se ejecute:** Notar que no tiene la clave ¨docs¨.  

<div style=“text-align: center;”><img src=https://i.imgur.com/6CJ4Flx.png></div>  

3- Luego **MySQL Connector** se pone a trabajar, revisa el mensaje enviado por produce, hace la consulta a MariaDB, actualiza el documento group_id indicado en la cola y por último envía un mensaje a la segunda cola indicándole el job_id y el group_id acaba de actualizar.  

**Como se ve el componente, recibe el mensaje de produce y envía otro mensaje a la segunda cola.**  

<div style=“text-align: center;”><img src=https://i.imgur.com/2V2RARb.png></div>  

**Así se vería el group luego de que MySQL Connector se ejecute y cumpla su trabajo de actualizarlo**  

<div style=“text-align: center;”><img src=https://i.imgur.com/pGrkSIU.png></div>  

4- El último pod llamado **consumer**, indica el mensaje que recibe de MySQL Connector por medio de la segunda cola. Indicando así que MySQL Connector cumple su rol de productor y consumidor de colas RabbitMQ.  

<div style=“text-align: center;”><img src=https://i.imgur.com/CSw0BAz.png></div> 

---

### Prueba unitaria del SQL Processor 
El SQL Processor realiza la tarea de Transform en un ETL pipeline, en este caso, el SQL Processor se traerá datos de una tabla para añadirlos al group especificado en el mensaje entrante de la cola. Esta prueba busca comprobar su funcionamiento de manera controlada e individual. El código ejecutado para la prueba se puede encontrar en el archivo *unitTestSQLProcessor*.py Para esta sección se tienen los siguientes datos en tablas de MariaDB:

#### Tabla de Personas:

<div style="text-align: center;"><img src=https://i.imgur.com/cyVms9l.png></div>

#### Tabla de Carros:

<div style="text-align: center;"><img src=https://i.imgur.com/WiDj8oK.png></div>


Se introduce un Job con los siguientes datos en el transformation de tipo sql_transform:

```json
{
    "name": "add_car",
    "type": "sql_transform",
    "table": "car",
    "expression": "SELECT %{field_description}% FROM %{table}% WHERE %{field_owner}% = %{doc_field}%",
    "source_data_source": "database_car",
    "destination_data_source": "destination_es",
    "doc_field": "id",
    "source_queue": "sql_queue",
    "destination_queue": "%{transform->transformation->myregex}%",
    "fields_mapping": {
        "field_description": "description",
        "field_owner": "owner"
}

```
#### Groups antes del procesado:
<div style="text-align: center;"><img src=https://i.imgur.com/IcL1uxS.png></div>

##### Resultados:
Se publica en la cola lo siguiente:

<div style="text-align: center;"><img src=https://i.imgur.com/G6omk2B.png></div>

Actualización del Group en elastic:

<div style="text-align: center;"><img src=https://i.imgur.com/11mcSC8.png></div>

Logs del componente:
<div style="text-align: center;"><img src=https://i.imgur.com/u4TxFep.png></div>


El codigo de las pruebas se puede encontrar en la dirección *.Images/SQLProcessor/unitTest/unitTestSQLProcessor.py*

---

### Prueba unitaria del Regex Processor
En esta sección se mostrará el proceso y resultado de las pruebas unitarias por parte del REGEX PROCESSOR. Este componente utiliza una cola por parte de RABBITMQ como fuente de información, a esta se le aplica el debido proceso de transformación, para finalmente en otra cola de RABBITMQ se envíe un mensaje como confirmación de que el trabajo de transformación ha finalizado.
Para este proceso se tiene un ambiente de prueba donde solamente se tienen los siguientes componentes:

* Cola Fuente
* Cola Destino
* REGEX PROCESSOR

Las pruebas que se visualizan en este archivo son un ejemplo específico del trabajo que es capaz de realizar el REGEX PROCESSOR, sin embargo no es el único, pues pueden haber infinidad de opciones por realizar; en este ejemplo se verá cómo es que se toma un mensaje de la cola de rabbitmq para ir a ElasticSearch, buscar la información necesaria que dentro de ella contiene un campo llamado "description" que contiene la información de un vehículo, al cual se le aplicará una expresión regular para obtener el código de placa del vehículo y agregarlo como nuevo campo al documento,  finalmente publicar un mensaje en otra cola de rabbitmq indicando que ya el proceso de transformación ha finalizado, para ese documento.

El archivo de nombre *test*.py que se puede encontrar en la carpeta *./Images/REGEXProcessor/unitTest* se tiene un código de prueba el cual toma mensajes de la cola y realiza transformaciones según se necesite para finalmente producir mensajes a la cola destino. Una vez con todos los datos de prueba en un flujo normal de datos se tiene:
<div style="text-align: center;"><img src=https://i.imgur.com/C5m5jJy.png></div>

Esto traducido en código, la ejecución del programa sería de la siguiente manera:
<div style="text-align: center;"><img src=https://i.imgur.com/dLVQtAN.png></div>

Los datos sin ninguna modificación en ElasticSearch para este ejemplo, se encuentran de la siguiente manera:
<div style="text-align: center;"><img src=https://i.imgur.com/xYpjVvI.png></div>

Luego de realizar el proceso de tranformación, el programa los deja publicados en ElasticSearch de la siguiente forma:
<div style="text-align: center;"><img src=https://i.imgur.com/keWsjFd.png></div>

Notese los puntos amarillos que contiene la imagen, son los datos que se han agregado a ese documento mediante el proceso de tranformación.

#### Pasos Para la Ejecución de las Pruebas
1. En la carpeta *./Images/REGEXProcessor/unitTest* ejecutar el archivo de python con el nombre **DATASET**, el cual genera datos de prueba para MariaDB.
2. En la misma carpeta, ejecutar el archivo de python con el nombre de **elasticdata**.
3. Por ultimo, ejecutar el archivo de python con nombre **test**.

---

### Prueba unitaria del Elasticsearch Publisher

En esta sección se explicará el proceso que se realiza en la prueba unitaria del componente Elasticsearch Publisher y los resultados de la prueba. El script se puede encontrar en la rama de *elasticsearch-publisher*, dentro de la carpeta de pruebas con el nombre *espublisher_pruebaUnitaria*.py.

Debido a que este componente representa la etapa Load del ETL Pipeline, para esta prueba se debe simular que ya ocurrieron las etapas anteriores; entonces se inicia con la publicación de un documento al índice jobs por parte de un usuario y luego se hace una simulación de que el Regex Processor (etapa de Transform) terminó su trabajo.

1. En el índice *jobs* de ES, el usuario publica el siguiente documento JSON.
[ejemplo01.json](https://estudianteccr-my.sharepoint.com/:u:/g/personal/andrealh17_estudiantec_cr/Ee_5KpvF5-hGroKX-C7gZj0BKcWeqJ4v9uuey7bB72e8AA?e=Xqa0p1)

2. El Regex Processor actualiza el documento en el índice *groups*, que queda de la siguiente manera.
<div style="text-align: center;"><img src=https://i.imgur.com/okvuujZ.jpg></div>


3. Este es el archivo JSON que recibirá el componente Elasticsearch Publisher en la cola de RabbitMQ.
<div style="text-align: center;"><img src=https://i.imgur.com/hFMT7mP.jpg></div>


Resultados


En la imagen se puede observar el estado de la cola antes de que se publique el mensaje a la cola que revisa el publisher, en la tabla la columna *Ready* se encuentra en 0. Cuando llega el mensaje a la cola de RabbitMQ, se inicia el proceso.

<div style="text-align: center;"><img src=https://i.imgur.com/DMEAWq0.jpg></div>

Resultados en consola del script de la prueba unitaria
<div style="text-align: center;"><img src=https://i.imgur.com/4QUtGrI.jpg></div>

Logs de la aplicación vistos desde Lens
<div style="text-align: center;"><img src=https://i.imgur.com/eksVdRn.jpg></div>



## Recomendaciones y conclusiones.

### Recomendaciones

1. Si se está trabajando con Windows, se recomienda limitar los recursos del Windows Subsystem For Linux (WSL) mediante un archivo de configuración *.wslconfig*, donde se puede especificar límites como la memoria; de esta manera nos aseguramos que programas como Docker no consuman la mayoría de los recursos de la computadora. 

2. Se recomienda realizar pruebas unitarias para cada componente de la aplicación con el fin de poder verificar el correcto funcionamiento de cada uno y propiciar una etapa de integración más eficiente y con menor cantidad de incovenientes. 

3. Al utilizar GitHub, se recomienda dedicar una rama a cada componente de una aplicación; en lugar de categorizar las ramas por miembro del equipo de trabajo si fuera el caso.  Esto permite mantener una mejor organización del proyecto y de las versiones del código de cada componente. 

4. Se recomienda utilizar la aplicación de escritorio Lens para administrar de una forma más visual los clusters de Kubernetes, al contar con una interfaz gráfica de usuario se aumenta la productividad y vuelve el proceso de depuración más eficiente.

5. Se recomienda utilizar diagramas para representar flujos de datos o de procesos en donde se necesite pues esto permite una mejor comprensión de la aplicación. 

6. Se recomienda que antes de iniciar con proyectos de este calibre, se realicen acuerdos entre los integrantes para definir cosas en común entre cada componente, como, por ejemplo, variables de entorno que se compartan entre componentes, de esta manera, se puede hacer solo un valor general que, si se modifica a uno, se le modifique a todos.

7. Para un componente como el orchestrator, se recomienda usar la función el método de `.process_data_events()` de la clase BlockingConnection de la biblioteca *“pika”* cuando se haga un ciclo no manejado por la misma librería. Esto debido a que no se mandaran las comprobaciones de RabbitMQ llamadas *”heatbeats”* que le avisan cuando una conexión sigue viva, por ende, hay que hacerlo manualmente.

8. Al manejar colas de RabbitMQ mediante la biblioteca *“pika”* en Python, se recomienda realizar *message acknowledgments*, los cuales se utilizan para notificar que un mensaje de la cola fue recibido exitosamente. En el proyecto se utilizó el método`basic_ack(delivery_tag=0, multiple=False)`. Donde el parámetro *delivery tag* puede ser un número entero y el parámetro *multiple* es para indicar si se va a notificar que se recibió exitosamente un mensaje (False) o un grupo de mensajes (True). En el proyecto se llama a esta función una vez que termina satisfactoriamente un proceso, una vez hecho esto, se va a consumir el siguiente mensaje en la cola. 

9. Dado que el componente MySQL Connector notifica que el *group* está listo antes que Elasticsearch, el documento que el SQL Processor utiliza no cuenta con el nuevo campo que se espera; por lo tanto, se recomienda crear dos variables de entorno. Una para la cantidad de intentos para iniciar el proceso y otra para definir el lapso entre cada intento. Entonces si el SQL Processor ha esperado mucho, lo descarta y pasa al siguiente *group*.

10. Se recomienda aprovechar la posibilidad de invitar colaboradores a los repositorios de las imágenes de Docker Hub, de esta forma se puede hacer *push* a las imágenes de otros integrantes del equipo y agilizar el proceso de integración o corrección de los componentes. 


### Conclusiones

1. El uso de servicios de mensajería como RabbitMQ, brindan una mejor visualización de la esencia del patrón de diseño productor consumidor; pues permite analizar cómo un componente de una aplicación puede ser tanto productor como consumidor. Por ejemplo, que una aplicación reciba de una cola, modifique el contenido del mensaje y luego publique el resultado a una cola. 

2. El uso de herramientas como Docker, Kubernetes y Helm Charts permite alcanzar altos niveles de automatización de soluciones, al utilizar estos elementos se pueden separar los componentes de una aplicación por contenedores, probarlos de forma independiente y administrar la carga de trabajo entre ellos buscando minimizar la cantidad de pasos manuales que se deban realizar al utilizar la aplicación. 

3. Las pruebas unitarias de los componentes de una aplicación representan una gran ventaja para proyectos, como el presente, donde se cuenta con variedad de componentes; entre sus ventajas se encuentra la agilización del proceso de integración de las partes, la posibilidad de realizar pruebas sin depender de otros componentes y tener pruebas a disposición para verificar modificaciones.

4. Tal vez pueda ser una mejor idea usar otra base de datos en lugar de Elasticsearch o buscar una manera de crear consistencia dentro de la misma. Esta al no tener consistencia, múltiples pods orchestrator pueden agarrar el mismo job, esto es inherente de las bases de datos NoSQL, pero puede provocar problemas con múltiples réplicas del orchestrator. La otra opción es manejar diferente los deployments del orchestrator y que se turnen para agarrar un doc nuevo.

5. Una buena documentación interna da un buen entendimiento para con las demas personas, al momento de trabajar en equipo y cada persona depende de otra, al momento de coordinar todas las partes es bueno tener claro que hace cada componente, pues no solamente al momento de juntar todas las partes se necesita ese conocimiento, sino al momento de las pruebas unitarias tenemos que saber que recibimos y qué enviamos a los otros componentes para comprobar que el nuestro funciona de buena manera.

6. Manejar archivos JSON en una aplicación resulta ventajoso por múltiples razones; por ejemplo, los datos se pueden acceder de forma sencilla y eficiente, la sintaxis es conveniente para los programadores debido a su sencillez y se puede implementar en gran variedad de lenguajes de programación.

7. Las métricas son pieza clave de los proyectos, estas ayudan en la ubicación sobre el funcionamiento del programa y podemos obtener distintas conclusiones. Si bien los logs de cada uno de los pods nos ayudan a saber que se encuentra haciendo en cada etapa del proyecto, las métricas nos dan otro tipo de datos mas cuantitativos, con ello se pueden tomar distintas decisiones como el levantamiento de mas pods consumidores en el caso de que la cola se esté llenando muy rápido, pero se vacía lento o por el contrario, si se llena lento y hay muchos consumidores podemos limitar su cantidad. En fin, son parte principal para la toma de decisiones sobre el desarrollo del proyecto.

8. El uso de Prometheus junto a Grafana es de gran relevancia para obtener datos útiles más allá de su aplicación en este proyecto, hoy en día tienen presencia en el *Business Intelligence*, que se refiere a la transformación de datos en información de manera que se busca mejorar el negocio; mientras Prometheus recolecta las métricas, Grafana brinda el elemento visual que hace más eficiente el análisis de datos. 

9. La implementación de *Pipelines Extract Transform Load* es importante para el futuro de los integrantes del grupo pues actualmente se utilizan para crear *Business Intelligence*, la cual es un área de relevancia donde se encuentran oportunidades como analista de datos o un propio analista de BI. 

10. El desarrollo de este tipo de proyectos es muy importante y valioso para cada uno de los integrantes del grupo, pues cada uno ha notado el fuerte crecimiento de los avances en tecnología y esto trae consigo nuevas formas de crear servicios; la arquitectura de microservicios es muy usada en los trabajos actuales, incluso hasta en muchos puestos de trabajo se necesita como mínimo, conocimiento básico con herramientas como Kubernetes o Helm Chart. Es por eso por lo que nosotros como equipo vemos un gran aprendizaje durante desarrollo de estas aplicaciones, usando conceptos vistos en clase y usados en el mundo actual. 


## Anexo 1: Referencias de Internet
Como es bien sabido, no somos conocedores de todas las soluciones ante todos los problemas, es por eso por lo que internet es una gran ayuda ante momentos donde necesitamos de algún tipo de apoyo en alguna sección de nuestro código.
En este apartado veremos las secciones de este proyecto dónde se ha utilizado código fuera de nuestra creación, el funcionamiento y la razón de por qué han sido tomados.
### Clase bcolors
Clase que modifica el color de la letra al momento de las impresiones en pantalla.
#### Código en el Programa
![](https://i.imgur.com/DAlLN6e.png)

#### Funcionamiento
Esta clase nos ayuda para que al momento de realizar impresiones dentro del programa, esto se logra escribiendo el color que necesitamos mostrar y el mensaje que se mostrara, después de haber realizado esto se debe reiniciar el color, esto ya que si no se hace todas las demás impresiones seguirán del mismo color seleccionado.
La clase original solamente contenía los color correspondidos a *[OK,WARNING,FAIL,RESET]*, sin embargo al momento de las pruebas unitarias se notó que hacían falta más colores, es por eso que la clase original ha sido modificada para tener mayor cantidad de opciones.

Un ejemplo práctico de su uso es:
```python!
print(f"{bcolors.OK} REGEX PROCESSOR: {bcolors.RESET} Process Finished")
```
#### Razón de Uso

La razón de su elección es para una mejor legibilidad de mensajes tipo logs que se verán sobre el pod en el momento que la aplicación se encuentre funcionando, pues ver texto plano es más difícil de leer, así que usar esta clase nos hace mas sencillo el proceso de lectura por parte del usuario para saber que esta haciendo el pod en cada momento.

### Convertir consulta sql a json.
Este código sirve para convertir una consulta sql a formato json. Indicando el campo de la fila como clave y su resultado como valor. 

#### Código en el programa:
![](https://i.imgur.com/SIrqbDP.png)

#### Funcionamiento:
Para el proyecto es muy útil este código pues convierte la consulta realizada por MySQL Connector a una lista en formato json que me indica la clave y valor. Por ejemplo si tenemos un registro en la tabla persona y hacemos un select * from persona, me devuelve: [{"cedula":Numero,"nombre":Nombre,"id":Numero,"provincia":Nombre,"canton":Nombre}].

#### Razón de Uso

La motivo por el cual se utiliza este código es por su simplicidad y por ser bastante compacto en los pasos que se realiza.

### USA_cars_datasets
Este no es un código como tal, sino mas bien un conjunto de datos para poder simular la información de ejemplo con la que se ha probado el programa, de esta se toma la información de automóviles y se genera el campo "description" para las bases de datos.

```python
def generateDescription():
    # reading CSV file
    data = read_csv(os.path.join(os.path.dirname(__file__), "USA_cars_datasets.csv"))
 

    br = data['brand'].tolist()
    md = data['model'].tolist()
    ye = data['year'].tolist()
    co = data['color'].tolist()
```


## Referencias bibliográficas

DelftStack. (17 de diciembre del 2020). *Texto de color impreso en Python*. Delft Stack. https://www.delftstack.com/es/howto/python/python-print-colored-text/

GeeksforGeeks. (27 de junio del 2022). *Print Colors in Python terminal*. https://www.geeksforgeeks.org/print-colors-python-terminal/ 

Kaggle. (22 de abril del 2020). *US Cars Dataset*. https://www.kaggle.com/datasets/doaaalsenani/usa-cers-dataset

Microsoft. (26 de septiembre del 2022). *Uso de MySQL Workbench para conectarse a los datos y consultarlos*. https://learn.microsoft.com/es-es/azure/mariadb/connect-workbench

Mount, B. (20 de julio del 2010). *Return SQL table as Json in python*. StackOverflow. https://stackoverflow.com/questions/3286525/return-sql-table-as-json-in-python
