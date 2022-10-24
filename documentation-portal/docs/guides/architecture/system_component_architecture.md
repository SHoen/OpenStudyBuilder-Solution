# System Component Architecture

[![System component architecture](~@source/images/documentation/studybuilder-system-components.svg)](../../images/documentation/studybuilder-system-components.svg)

The system is composed by the following components.

| System Component <br> (License) | Technology <br> (Git repository) | Description |
| ------ | ------ | ------------------ |
| StudyBuilder App <br> (GPLv3)     | Vue.js using Vuetify library <br> (studybuilder) | JavaScript based web application with the UI for creating the study definition specification, maintaining library standards. The StudyBuilder app holds two main modules: <br> - Library <br> - Studies | 
| StudyBuilder Documentation Portal <br> (GPLv3) | Vuepress <br> (documentation-portal) | Markdown based documentation portal with StudyBuilder Introduction, User Guides, System Documentation, Data Models and more. |
| Clinical MDR API Specification <br> (MIT) | OpenAPI Specification / Swagger <br> (clinical-mdr-api-spec) | Online documentation of the API. |
| Clinical MDR API <br> (GPLv3) | Phyton using FAST API framework <br> (clinical-mdr-api) | Python based web application based on FAST API framework supporting all CRUD actions to the database, access control, versioning, workflows and data integrity rules. |
| Clinical MDR <br> (MIT) | Cypher <br> (neo4j-mdr-db) | Clinical MDR logical and physical data models, database constraint definitions, procedures and functions. |
| Graph Database <br> (Neo4j free edition or licenced enterprise edition) | Neo4j native graph database <br> (neo4j.com) |
| CDISC Library Standards Import <br> (GPLv3) | Python and Cypher <br> (mdr-standards-import) | Import programs connecting to CDISC Library, downloading files to cloud storage, reading these into staging database, and then inserting data into Clinical MDR database. |
| Data Import <br> (MIT) | Python and Cypher <br> (data-import) | Import programs using .csv or JSON files as input for importing various data into the Clinical MDR database. The import programs can import JSON files exported from the system, in this way data can be moved between environments. All import actions are done via calls to the Clinical MDR API, so all import actions will be audit trailed. |

> - MIT: MIT license is a permissive free software license originating at the Massachusetts Institute of Technology (MIT).<br>For more info see: https://opensource.org/licenses/MIT

> - GPLv3: GPLv3 license is a GNU General Public License. The GPL series are all copyleft licenses, which means that any derivative work must be distributed under the same or equivalent license terms.<br>For more info see: https://opensource.org/licenses/GPL-3.0 and https://www.gnu.org/licenses/quick-guide-gplv3.html

