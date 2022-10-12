FROM python:3.10.7-slim-bullseye

WORKDIR /app

COPY app/. .

RUN apt-get update -y
RUN apt-get install -y wget
RUN apt-get install -y curl
run apt-get install -y build-essential
RUN wget https://downloads.mariadb.com/MariaDB/mariadb_repo_setup
RUN chmod +x mariadb_repo_setup
RUN ./mariadb_repo_setup \
   --mariadb-server-version="mariadb-10.6"

RUN apt-get install -y libmariadb3 libmariadb-dev
RUN pip install mariadb

CMD ["python","-u","./app.py"]