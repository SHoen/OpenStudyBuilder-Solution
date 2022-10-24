# Status quo of the OpenStudyBuilder
The OpenStudyBuilder solution introduces a new approach for working with studies that once fully implemented will drive end-to-end consistency and more efficient processes - all the way from protocol development and CRF design - to creation of datasets, analysis, reporting, submission to health authorities and public disclosure of study information.

OpenStudyBuilder is the first MVP of the solution covering the foundational capabilities for the front-end application, the data standards and study definition repository as well as the initial integrations.

OpenStudyBuilder is the open source version of the internal StudyBuilder solution at Novo Nordisk. Not all titles or logos in the application are yet changed to be 'OpenStudyBuilder' - when the term 'StudyBuilder' is used, it is therefore a synonym for 'OpenStudyBuilder'. This will be changed in coming updates.

# Introduction
StudyBuilder consists of a few main components, that are all included as subdirectories in this repository.

- neo4j-mdr-db: Configuration files and initialization scripts for the Neo4j database.
- mdr-standards-import: Scripts for populating the database with clinical standards.
- clinical-mdr-api: The Python/FastAPI backend.
- data-import: Python scripts for populating the database with sponsor standards and codelists.
- studybuilder: The Vue.js frontend.
- documentation-portal: Project documentation.

Each directory contains a more detailed readme for that component.

# This repository
This is a build (Docker) project for the complete StudyBuilder application.
The project is used to combine multiple repositories into a single folder structure
to make is possible to use docker compose and builds across the different repos.

Currently the following containers are part of the docker compose solution.

- database (A neo4j graph database container including a initial data load)
- api (A fastAPI container hosting the clinical-mdr-api application)
- frontend (A nginx container hosting Vue.js StudyBuilder client application)
- documentation (A nginx container hosting Vue.js Study Builder documentation portal)
- sonarqube (A container a Sonarqube server for code validation. This is not started by default)

# Getting Started
## Overview
A number of steps must be performed in order to get the StudyBuilder application running.
This can either be accomplished by using docker-compose as descibed in [Build and Test](#build-and-test),
or by manually performing the following steps in the listed order. Note that it is also possible to run step 5 before step 4, but for performance reasons it's still recommended to run them in the listed order.

1. Start and initialize the database.

   See the readme in the `neo4j-mdr-db` directory.
   This will start the database and prepare it for use.

2. Populate the database with clinical standards.

   This imports all CDISC terms.
   Follow the instructions in the `mdr-standards-import` directory.
   The import is performed by directly accessing the Neo4j database,
   and the FastAPI backend is not required.

3. Start the API.

   See the readme in the `clinical-mdr-api` directory.
   This starts the backend that provides the StudyBuilder API as well as
   exposing the Swagger UI with auto-generated API documentation.

4. Populate the database with sponsor standards.

   This creates all needed codelists in the sponsor library.
   It also includes a set of mockup data to create example projects, studies etc.
   Follow the instructions in the `data-import` repository.
   This step performs the import by calling the StudyBuilder API,
   and thus the backend must be running.

5. Start the frontend.

   See the readme in the `studybuilder` directory.

6. All done.

   The StudyBuilder GUI should now be accessible by pointing a brower at
   the host and port used in [step 5](#start-the-frontend).


## Software dependencies

A Docker environment with at least 6GB of docker memory allocated is required.
The solution is tested on Ubuntu and Windows (WSL 2) docker environment.
It can be either Docker Desktop or docker binaries that can run
docker compose version 3.9 files and related docker commands.
The following docker environments have been tested:

Windows 11 - Docker version: 20.10.17, Docker compose version: 2.7.0 (WSL 2 configuration)

Ubuntu 20.04 - Docker version: 20.10.17, Docker compose version: 2.6.0

To list Docker version use: `docker version` and `docker compose version`

Windows installation link: [Windows installation](https://docs.docker.com/desktop/install/windows-install/)

Ubuntu installation link: [Ubuntu installation](https://docs.docker.com/engine/install/ubuntu/)

To test your local docker installation run the following command
in a non administrator or root shell: `docker run hello-world`

If this is not working see this link for Ubuntu rootless configuration:
[Docker Rootless](https://docs.docker.com/engine/security/rootless/)

For low-end systems, the database container may fail.
If this happens, change the following three lines of `databasedockerfile`:
```
RUN echo dbms.memory.heap.initial_size=2g >> /var/lib/neo4j/conf/neo4j.conf \
 && echo dbms.memory.heap.max_size=2g >> /var/lib/neo4j/conf/neo4j.conf \
 && echo dbms.memory.pagecache.size=2g >> /var/lib/neo4j/conf/neo4j.conf \
```
Instead of `2g`, use a lower value, such as `1g` or `500m` etc., depending on the system.
This will affect the performance of the neo4j database.

On Windows installations the WSL engine can take up all system resources.
It is recommended to configure limits. Create a `.wslconfig` file in the user directory, typically `C:\Users\username\`.
Put the following content in the `.wslconfig` file, and change `memory` to a suitable value for the given system. Half the physical RAM is a good starting point.
```
[wsl2]
processors=2
memory=6GB
```
See [Advanced settings configuration in WSL](https://docs.microsoft.com/en-us/windows/wsl/wsl-config)
for all available options.

# Build and Test

By this point, you should have a Git clone of the OpenStudyBuilder-solution repo or a zip file with complete folder structure including subcomponents.
If you don't have that, jump back to the [Getting Started](getting-started) section above.

Your folder structure should look like this:
```
─ OpenStudyBuilder-solution
  ├─ clinical-mdr-api
  ├─ data-import
  ├─ documentationfiles
  ├─ documentation-portal
  ├─ frontendfiles
  ├─ mdr-standards-import
  ├─ neo4j-mdr-db
  └─ studybuilder
```

Use the docker-compose.yml file in the root folder (OpenStudyBuilder-solution) to build
and bring up the environment with this docker command:
`docker compose up -d --build`

**NOTE** The docker-compose build runs the steps 1, 2, 3 and 5 listed in [Overview](#overview).
Step 4, the import of sponsor standards, must still be run after the environment has been brought up. See the readme in the `data-import` directory for instructions.
This means that step 4 runs after step 5, which is possible but makes the import run slightly slower.

If a local Sonarqube server is also needed use this docker command:
`docker compose up -d --build sonarqube`

Initial build can take up to 15 min. or more depending on computer resources
and internet network bandwidth.

After build is complete the api container will restart a few times
until the neo4j database is running and accessible.
During this process, the API will throw an error if it attempts to connect to the DB
before it has finished booting up, and will then try again after a small break.
If you run docker-compose detached from the console (using the `-d` flag),
you will not see this error, but the localhost API port will not be available
before the API is able to contact the DB.

To validate that the environment is running use this docker command:
`docker container ls`

This should show an output looking something like this:
```
IMAGE                       COMMAND                  CREATED              STATUS              PORTS
OpenStudyBuilder-solution_documentation   "/docker-entrypoint.…"   About a minute ago   Up About a minute   80/tcp, 0.0.0.0:5006->5006/tcp, :::5006->5006/tcp
OpenStudyBuilder-solution_frontend        "/docker-entrypoint.…"   About a minute ago   Up About a minute   80/tcp, 0.0.0.0:5005->5005/tcp, :::5005->5005/tcp
OpenStudyBuilder-solution_api             "uvicorn clinical_md…"   About a minute ago   Up 47 seconds       0.0.0.0:5003->5003/tcp, :::5003->5003/tcp
OpenStudyBuilder-solution_database        "/sbin/tini -g -- /d…"   About a minute ago   Up About a minute   7473-7474/tcp, 0.0.0.0:5001-5002->5001-5002/tcp,
```

To access the application the following links can be used:

- Study Builder main application: <http://localhost:5005/>

- Study Builder documentation: <http://localhost:5005/doc/>

  It can also be accessed from main web application from the ? sign in top right.
  Is also directly exposed on <http://localhost:5006/>

- API backend: <http://localhost:5005/api/docs>

  FastAPI requests documentation. Is also directly exposed on <http://localhost:5003/docs>

- Neo4j database web client: <http://localhost:5001/>

  Username and password default is user: `neo4j` and password: `secret1234`

- Neo4j database bolt connection: <neo4j://localhost:5002>

  The main neo4j database is named `mdrdb`.

- Sonarqube server: <http://localhost:9000/>

  Username and password default is user: `admin` password: `admin`

To stop the environment again use these docker commands (Due to multiple profiles):
```
docker compose stop
docker compose down -v
docker compose rm -f
```

To restart the environment again without rebuilding use this docker command:

`docker compose up -d`

or

`docker compose up -d sonarqube`

To clean up the entire docker environment use the following commands (**Will delete, volumes and cache NOT only Clinical MDR related docker components.**)

```
docker rmi $(docker images --filter=reference="*_database" -q) -f
docker rmi $(docker images --filter=reference="*_api" -q) -f
docker rmi $(docker images --filter=reference="*_frontend" -q) -f
docker rmi $(docker images --filter=reference="*_documentation" -q) -f
docker rmi $(docker images --filter=reference="*_sonarqube" -q) -f
docker volume prune (Will delete all volumes not used, only needed if -v was not used on docker-compose down command)
docker builder prune --all (Will clean all docker cache files)
```

# Using this setup for development
If you're working on a change for the studybuilder frontend,
you might only want the database and api containers running
and connect to those from your local studybuilder instance.
```
docker compose build
docker compose up api
```
This will build all containers and then start the `api` and dependant containers (the database).

Similarly, if you want to develop the API or test API functionality,
you can simply boot up the database:
```
docker compose up database
```

The names used for single components of the system here corresponds to
the container names (`container_name`) within the docker-compose file.

The names are:
- database
- api
- frontend
- documentation
- sonarqube
