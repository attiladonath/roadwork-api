# Local development

## Required extra packages on Ubuntu

For PostgreSQL and Shapely:

```
apt-get install libpq-dev libgeos-dev
```

## Database

Use Docker to setup a PostgreSQL database with PostGIS extension.

See: https://hub.docker.com/r/mdillon/postgis/

```
docker run --name postgres -p 5432:5432 mdillon/postgis
```

Then connect to the database server.

```
psql -h localhost -U postgres
```

Create a new database from the template given by the above Docker project.

```
CREATE DATABASE roadwork_api TEMPLATE template_postgis;
```

## Python

Use Python version 2.7

Setup virtualenv:

```
pip install virtualenv
virtualenv virtualenv
. virtualenv/bin/activate
```

Install required modules:

```
pip install -r requirements.txt
```

Setup environment variables:

```
. init.sh
```

Initialize database:

```
flask db upgrade
```

Run the application:

```
flask run
```

By default you can access the app under: http://127.0.0.1:5000/

## Swagger UI

```
docker run -p 8080:8080 swaggerapi/swagger-ui
```

It will be available under: http://localhost:8080/

Load the Swagger YAML file into Swagger UI: http://127.0.0.1:5000/swagger.yaml
