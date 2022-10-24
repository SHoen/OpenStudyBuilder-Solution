# Introduction 
As part of the Clinical MDR project, this repository takes care of the import of
* the controlled terminology (CT) from CDISC.

Later on, other imports like UNII, SNOMED, etc. might be added.

# Local Setup

## Setup python virtual environment

* Make sure python 3.7 and pipenv is installed on your machine. Installation guide can be found
 [here](https://dev.azure.com/novonordiskit/Clinical-MDR/_git/neo4j-mdr-db?path=/README.md&version=GBUpdate_README) under section Python Getting Started.
* Run `pipenv install`
---
## Setup environment variables

Create `.env` file (in the root of the repository) with the following content (adjust accodingly):

```
#
# Neo4j Database
#
NEO4J_MDR_BOLT_PORT=5078
NEO4J_MDR_HOST=localhost
NEO4J_MDR_AUTH_USER=neo4j
NEO4J_MDR_AUTH_PASSWORD=test1234
NEO4J_MDR_DATABASE=neo4j

NEO4J_CDISC_IMPORT_BOLT_PORT=5078
NEO4J_CDISC_IMPORT_HOST=localhost
NEO4J_CDISC_IMPORT_AUTH_USER=neo4j
NEO4J_CDISC_IMPORT_AUTH_PASSWORD=test1234
NEO4J_CDISC_IMPORT_DATABASE=cdisc-ct

#
# CDISC API
# API token is not mandatory as the package
# folder is now placed in the repository
#
CDISC_BASE_URL="https://library.cdisc.org/api"
CDISC_AUTH_TOKEN="<<Insert secret here>>"

#
# Download folder for the CDISC JSON package files
#
CDISC_DATA_DIR="cdisc_data/packages"
```

**Note:** Bolt port number might need to be changed for different cutomised setup, but the above could do the trick for basic setup. 

---

## Neo4j database setup

### CDISC CT DB

The CDISC CT DB will be created automatically including the index configuration. Nothing to do here.

### MDR DB

The MDR DB needs to be present and need to have the correct index configuration. See the instructions in the `neo4j-mdr-db` repository 
[README](https://dev.azure.com/novonordiskit/Clinical-MDR/_git/neo4j-mdr-db?path=/README.md&_a=preview) 
, after the step of `Initiate neo4j database` should do the trick basically.

## CDISC CT Data

* Download CT Packages from the CDISC REST API by running:
```shell
pipenv run python -m mdr_standards_import.cdisc_ct.dev_scripts.download_json_data_from_cdisc_api 'your-sub-directory'
```

**Note:** This step can be skipped as the JSON package files is now placed in the repository and will be downloaded when you clone the repository.
This is to avoid high usage of the CDISC API, as there is a rate-limit in place..
---

## Development Entrypoints

### Import data to both CDISC CT and MDR database
The following command will:
* skips the download from the CDISC CT REST API
* triggers the import into the CDISC CT DB
* triggers the import into the MDR DB

```shell
pipenv run python -m mdr_standards_import.cdisc_ct.dev_scripts.bulk_import 'TEST' '' true
```


### Import data to only CDISC CT database

The following command will:
* skips the download from the CDISC CT REST API and
* triggers the import into the CDISC CT DB

```shell
pipenv run python -m mdr_standards_import.cdisc_ct.pipelines.pipeline_step_import_cdisc_ct_into_cdisc_ct_db 'TEST' '' true
```

### Import data to only MDR database

The following command will:
* triggers the import into the MDR DB

```shell
pipenv run python -m mdr_standards_import.cdisc_ct.pipelines.pipeline_step_import_from_cdisc_ct_db_into_mdr 'TEST' '2021-09-24'
```

---

## Verify setup is complete
* Open Neo4j browser in your web browser at the address: http://localhost:5074/ (http://NEO4J_MDR_HOST:NEO4J_MDR_BOLT_PORT), log in with username and password stated in .env file in neo4j_database repository (default is username: neo4j, password: test1234)
* Switch to database cdisc-ct, run command:
```
MATCH (p:Package)-[:CONTAINS]->(c:Codelist) WHERE c.effective_date=date("2015-12-18")
WITH p.name as name, count(c) AS count
RETURN name, count
```
* The output should be:
```
name	                count
"SDTM CT 2015-12-18"	480
"SEND CT 2015-12-18"	92
"ADAM CT 2015-12-18"	7
```
* Switch to database neo4j, run command:
```
MATCH (c:CTPackage)-[:CONTAINS_CODELIST]->(cc:CTPackageCodelist) WHERE c.effective_date=date("2015-12-18")
WITH c.name as name, count(cc) AS count
RETURN name, count
```
* The output should be the same as before:
```
name	                count
"SDTM CT 2015-12-18"	480
"SEND CT 2015-12-18"	92
"ADAM CT 2015-12-18"	7
```

---

# More information on CDISC CT Import

For more information on pipeline configuration, see the `*.yml` files in the root of the repository.

For more information on on the overall setup, see the section `CDISC CT Integration` in the documentation portal.

For more information on scripts definitions, see the [Pipfile](./Pipfile).


## Pipeline Steps

```shell
pipenv run import_cdisc_ct_into_cdisc_ct_db <user initials> <JSON directory name> <skip download step>
```

```shell
pipenv run import_from_cdisc_ct_db_into_mdr <user initials> <effective date>
```
---

## Further Development Commands

- drops the *intermediate* CDISC CT DB
```cypher
DROP DATABASE `cdisc-ct` IF EXISTS
```

- deletes everything in the currently selected DB
```cypher
CALL apoc.periodic.iterate('MATCH ()-[r]->() RETURN id(r) AS id', 'MATCH ()-[r]->() WHERE id(r)=id DELETE r', {batchSize: 50000});
CALL apoc.periodic.iterate('MATCH (n) RETURN id(n) AS id', 'MATCH (n) WHERE id(n)=id DELETE n', {batchSize: 50000});
```