# Introduction 
This repository is used for utilities and scripts for initializing the Neo4j MDR Database with test data.


# Python Getting Started

This project uses https://github.com/pypa/pipenv for dependencies
management, so you must install it on your system (version 2020.8.13 or later, ubuntu apt ships and old version so use pip to install pipenv)

```
$ python3 --version
$ pip --version
$ pip install pipenv
```
**Note:** In case your system has newer version of python than 3.7 (e.g. 3.8 as of Ubuntu 20.04), you can install version 3.7 (leaving system default intact) with:
```
$ sudo add-apt-repository ppa:deadsnakes/ppa
$ sudo apt-get update
$ sudo apt-get install python 3.7
```


# Running
## Preparations

These migration scripts populate the database via the backend. Thus they require both the Neo4j database and the clinical-mdr-api to be running.

Follow Backend development process overview section in [Development Process Wiki](/Agile-Delivery-Model/Development-Process) to setup other repositories.

After finishing the setup of the other repositories, start the API with the command described in the API repository README file and then run the following command to start migrations.

## Setup environment variables
Create `.env` file (in the root of cloned repository). Use the `.env.import` file as a template and adjust as needed.

**Note:**
If you run neo4j desktop, the defaults ports are
```
NEO4J_MDR_HTTP_PORT=7474
NEO4J_MDR_BOLT_PORT=7687
```
API_BASE_URL depends on whether each component is run separately or if docker-compose is used. Make sure your reference is correct, such as:
```
API_BASE_URL=http://localhost:5003
```
Or with redirection from the frontend (docker-compose setup):
```
API_BASE_URL=http://localhost:5005/api
```

## Activate pipenv

Activate pipenv by running:

```
$ pipenv install
```

## Run full import
Run the following command to start the full import.

```sh
$ pipenv run import_all
```
**Note:** This will take some time to run.

## Partial import

It is also possible to run only a single part of the import with ```pipenv run {scriptname}```. The available commands are listed under `[scripts]` in the `Pipfile`.

The current set of commands is:
- import_all (runs all of the others)
- config
- dictionaries
- activities
- codelistterms1
- codelistterms2
- unitdefinitions
- codelistfinish
- compounds
- mockdata
- mockdatajson


# Import steps
## Outline
- "general" stuff like snomed and ucum libraries, and field configs
- create "standard" codelists in sponsor library by collecting (mostly) CDISC terms.
- import compounds ()
- (optional step) novo-specific sponsor stuff
- mock data (studies and projects etc)

## Steps
## Dictionaries
- libraries
  - MDR_MIGRATION_DICTIONARIES_CODELISTS_DEFINITIONS

- snomed
  - MDR_MIGRATION_SNOMED

- med rt
  - MDR_MIGRATION_MED_RT

- unii
  - MDR_MIGRATION_UNII

- ucum
  - MDR_MIGRATION_UCUM


## General config

- study field config
  - MDR_STUDY_FIELDS_DEFINITIONS

## Additions to codelists

- Additional terms for the frequency codelist, C71113
  - MDR_MIGRATION_FREQUENCY

## Sponsor library content, standard codelists

- sponsor codelist definitions. Used to create the lists, no content here.
  - MDR_MIGRATION_SPONSOR_CODELIST_DEFINITIONS

- operator (equal, larger than, etc)
  - MDR_MIGRATION_OPERATOR

- epoch (collect terms from cdisc in sponsor codelist, add a few terms not in cdisc)
  - MDR_MIGRATION_EPOCH
  - MDR_MIGRATION_EPOCH_TYPE
  - MDR_MIGRATION_EPOCH_SUB_TYPE

- endpoint
  - MDR_MIGRATION_ENDPOINT_LEVEL

- endpoint (sub) cathegory
  - MDR_MIGRATION_ENDPOINT_CATEGORY
  - MDR_MIGRATION_ENDPOINT_SUB_CATEGORY

- activity
  - MDR_MIGRATION_ACTIVITIES
  - MDR_MIGRATION_ACTIVITY_SUB_GROUPS
  - MDR_MIGRATION_ACTIVITY_GROUPS
  - MDR_MIGRATION_ACTIVITY_INSTANCES (TODO move to mock data??)

- objective
  - MDR_MIGRATION_OBJECTIVE_LEVEL

- codelist parameter set, used to mark codelist terms as template parameters
  - MDR_MIGRATION_CODELIST_PARAMETER_SET

- arm type
  - MDR_MIGRATION_ARM_TYPE

- criteria type
  - MDR_MIGRATION_CRITERIA_CATEGORY
  - MDR_MIGRATION_CRITERIA_SUB_CATEGORY
  - MDR_MIGRATION_CRITERIA_TYPE

- compound dispensed in
  - MDR_MIGRATION_COMPOUND_DISPENSED_IN

- device
  - MDR_MIGRATION_DEVICE

- dosage form, define sponsor preferred names for cdisc terms
  - MDR_MIGRATION_DOSAGE_FORM

- element (sub)type
  - MDR_MIGRATION_ELEMENT_TYPE
  - MDR_MIGRATION_ELEMENT_SUBTYPE

- flowchart group
  - MDR_MIGRATION_FLOWCHART_GROUP

- objective cathegory
  - MDR_MIGRATION_OBJECTIVE_CATEGORY

- therapy area
  - MDR_MIGRATION_THERAPY_AREA

- time reference
  - MDR_MIGRATION_TIME_REFERENCE

- type of treatment
  - MDR_MIGRATION_TYPE_OF_TREATMENT

- sponsor defined units (extending SDTM)
  - MDR_MIGRATION_SPONSOR_UNITS

- unit definitions
  - MDR_MIGRATION_UNIT_DIF

- unit dimension
  - MDR_MIGRATION_UNIT_DIMENSION

- unit subset
  - MDR_MIGRATION_UNIT_SUBSETS

- visit contact mode
  - MDR_MIGRATION_VISIT_CONTACT_MODE

- visit type
  - MDR_MIGRATION_VISIT_TYPE

- visit sub label
  - MDR_MIGRATION_VISIT_SUB_LABEL

- null flavor
  - MDR_MIGRATION_NULL_FLAVOR

## CRFs
- crf templates
  - MDR_MIGRATION_ODM_TEMPLATES
- forms
  - MDR_MIGRATION_ODM_FORMS
- groups
  - MDR_MIGRATION_ODM_ITEMGROUPS
- items
  - MDR_MIGRATION_ODM_ITEMS

## Sponsor terms, NN specific (for now) 
- compounds
  - MDR_MIGRATION_COMPOUNDS

## Mock data
Set up some mock data to have something to show.

- studies
  - MDR_MIGRATION_STUDY
  - MDR_MIGRATION_STUDY_TYPE

- projects
  - MDR_MIGRATION_PROJECTS

- objectives
  - MDR_MOCKUP_OBJECTIVES_OBJECTS

- endpoints
  - MDR_MOCKUP_ENDPOINTS_OBJECTS

- timeframes
  - MDR_MOCKUP_TIMEFRAMES_OBJECTS

- study objectives
  - MDR_MOCKUP_STUDY_OBJECTIVES

- study endpoints
  - MDR_MOCKUP_STUDY_ENDPOINTS

### Exported data from json
TODO rename the script!
This data is exported by the [studybuilder-export](https://dev.azure.com/novonordiskit/Clinical-MDR/_git/studybuilder-export) script.
What files to use is configured by a single variable that points to the exported project listing.
Other files are found via their names that match their corresponding endpoints. 

- projects listing
  - IMPORT_PROJECTS="datafiles/mockup/exported/projects.json"

#### Selective import

There are a number of options for limiting what is imported from json. 
The different parts can be skipped by setting the corresponding variable to `False`.
When importing studies, there are two variables for selecting which studies are imported. 
`INCLUDE_STUDY_NUMBERS` is used to select which study numbers are included,
while `EXCLUDE_STUDY_NUMBERS` is used to exclude. 
The logic is that it first filters the available studies to include 
only the ones in `INCLUDE_STUDY_NUMBERS`. 
If `INCLUDE_STUDY_NUMBERS` is not specified, then all are included.
After this it then removes any study listed in `EXCLUDE_STUDY_NUMBERS`.
Both accept a comma-separated list of study numbers, like `1001,1002,1234`.

```
MDR_MIGRATION_EXPORTED_PROGRAMMES=True
MDR_MIGRATION_EXPORTED_BRANDS=True
MDR_MIGRATION_EXPORTED_ACTIVITIES=True
MDR_MIGRATION_EXPORTED_UNITS=True
MDR_MIGRATION_EXPORTED_COMPOUNDS=True
MDR_MIGRATION_EXPORTED_TEMPLATES=True
MDR_MIGRATION_EXPORTED_PROJECTS=True
MDR_MIGRATION_EXPORTED_STUDIES=True
INCLUDE_STUDY_NUMBERS=""
EXCLUDE_STUDY_NUMBERS=""
```

#  Authentication

Supports [OAuth 2.0 client credentials flow with shared secret](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow#first-case-access-token-request-with-a-shared-secret).
Credentials can be configured by setting all the following environment variables.
If *CLIENT_ID* is set, the authentication routine is activated.

```shell
CLIENT_ID="aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
CLIENT_SECRET="...FILL-ME..."
TOKEN_ENDPOINT="https://login.microsoftonline.com/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/oauth2/v2.0/token"
SCOPE="api://aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/.default"
```

- **TOKEN_ENDPOINT** is the endpoint where to post the authentication request.
  Can be found in the OpenID Connect metadata document, or Azure Active Directory -> App registrations -> Endpoints.
- **SCOPE** is the scope to request at the authentication flow, and in case of the Microsoft Identity Platform,
  that is the application ID (in URI format) of the API and *.default*
  The main point here is that the OAuth authority should give back a valid access token.
- **CLIENT_ID** is the application id registered for this client application
- **CLIENT_SECRET** is one of the secret key values set up with the client application at the authority

Authentication is done once per migration script session, fetching an access token which is then included in each
request as the *Authorization* header.

# Sample data and scripts

There is a selection of sample Cypher scripts that are useful for testing
and learning more about Cypher and the datamodel. See the `sample_scripts` folder.
These scripts rely on some files in the `datafiles/libraries/concepts/crfs` and `migration_test_data\unused` folders.
