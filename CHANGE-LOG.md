# OpenStudyBuilder Commits changelog


## V 0.8.1

## New Features
- Initially one NeoDash report is included in the deployment process into the database. The NeoDash report can be opened when connecting manually to the database, see system user guide. Short NeoDash userguide added on the documentation protal.
- Under Library, Admin Definitions new pages support maintenance of Clinical Programmes and Projects.

## Feature Enhancements

### General
- Release number correctly displayed on About page. Various minor improvements to table displays.

### Studies
- Empty column is added to the Protocol SoA to support manual references to protocol sections.
- Add display of additional timing variable in Study Visits table. If a footnote is added to a level, that is hidden for the protocol SoA, then the footnote letter should be carried up to the next level above.  Hide retired library activities from the listing on the Add new study activity from library form.  Add unit name in API response for /concepts/numeric-values-with-unit.  Return all code lists for a CT term in API response from /ct/terms/{term_uid}/names.
- Possibility to control the display of the SoA groups in the Protocol SoA from the detailed SoA. Improved filtering on activity group and subgroup. DocX generation supported for Detailed SoA and available for download together with .csv files.
- All pages under Define Study menu now supports display of a released or locked study.
- Study Structure, Study Activities and Study Interventions pages also support display only views that can be used by all user groups including users with view only access.
- Under Manage studies the system supports defining sub part studies for a parent study, thereby supporting study definitions covering multiple parts with independent study design, SoA, etc.

### Libraries
- Performance Improvements done for Syntax Templates to work bit faster and to achieve better user experience.
- Additional attributes and minor improvements to activity request form (activity placeholders).
- Support multiple groupings can be defined for activity concepts.
- Improvements of sponsor preferred names for a number of CDISC controlled terminology as part of sample datasets.
- Overview pages for activities and activity instances now include an simple CDISC COSMoS YAML display page with a download option. Overviews are improved including cross reference hyperlinks.
- Uppercase first letter in template instantiation when first text is a Template Parameter.
- Add permanent filters on Library/concept/activities/List of activities and Activities Instances. Avoid overwriting existing choices in batch edit functionality in detailed SoA. Improve About StudyBuilder page front end. Option to go one step back in Library overview pages. Correct sorting of project ID when adding studies. Change key criteria column in criteria template table to Yes/No from True/False and include selection of value to edit dialogue. Update display of SBOM in About page.

### API
- Refactoring parts of the API code, including reduction of the number of calls made by the backend to the DataBase, to improve loading times when working with syntax templates
- API support study activity instances as part of the Operational SoA, UI implementation will follow in next release.
- Implement support for additional registry identifiers in API (UI implementation will follow in next release).
- Indexes and constraints added to the database to improve query performance. This reduces loading times for the various pages related to syntax templates in the front-end.


## Bug Fixes

### API
-  StudyBuilder Production Application stops working due to API logging overloaded
-  API cannot find correct authentication key after keyrotation.
-  Clearing a StudyField get recorded in a non-standard way in audit trail.
-  DELETE /ct/terms/{term_uid}/attributes/activation -> Unable to retire a term that is not included in the latest CT Package.

### DB Schema migration
- Missing relationships in Activities in the Library

### Library
-  Code Lists -> CT Packages:  Viewing code lists in past CDISC packages does not include all terms.
-  Code Lists -> CT catalogues: 502 error appearing several times (Temporary fix applied).
-  Concepts -> Activities: Default filters are bypassed when changing some other filtering parameter.
-  Concepts -> Activities: Error when filtering out Activity Group in Activity Subgroups tab.
-  Concepts -> Activities: The history pages of Activity Instances do not show Activity name.
-  Concepts -> Units: It is not possible to filter units on Unit Subset.
-  Concepts ->Activities: Handling placeholder request form greyes out.
-  Concepts ->Activities: Possible to select draft activities while creating and editing activity instances.
-  Syntax Templates -> Criteria Templates: When exporting preinstance templates to Excel the exported file contains no data and the column headers are not releated.
-  Syntax Templates -> Criteria templates: When downloading Inclusion Criteria pre-instances only the column headers are included in the downloaded file.

### Studies
-  Define Study -> Study Activities: Adding activities from other studies - "Requested" activities cannot be added by other studies
-  Define Study -> Study Activities: After adding activity placeholders, system does not allow to hide activity grouping
-  Define Study -> Study Activities: Creating activity placeholders without activity group and subgroup gives an error
-  Define Study -> Study Activities: Not possible to change preferred time unit in visit overview
-  Define Study -> Study Activities: Sorting of reference visit for special visit is not in ascending order
-  Define Study -> Study Activities: Retired' and 'Draft' activities are also shown by default in the 'Add study activities' window
-  Define Study -> Study Activities: Batch editing several activities in Detailed SoA sometimes adds an activity to more visits than selected
-  Define Study -> Study Activities: Clicking on the Protocol SoA tab returns an error in some cases
-  Define Study -> Study Activities: Default filters are bypassed when changing some other filtering parameter in the pop-up window to Add study activities from Library
-  Define Study -> Study Activities: It is not possible to filter on more than one column at a time when adding Activities from Library on the Study Activities tab
-  Define Study -> Study Activities: Performance issues when grouping visits on the Detailed SoA tab
-  Define Study -> Study Activities: Studies in production cannot remove activities 
-  Define Study -> Study Activities: The export of Study Activities do not include information in all columns
-  Define Study -> Study Activities: User is not directed back to the Edit dialogue after saving the footnote assignment on the Detailed SoA page
-  Define Study -> Study Activities: When adding activities from library, the filter put to selecting study activities is showing final activity request that have not yet been approved.
-  Define Study -> Study Activities: When creating a placeholder for a new activity request then it is possible to select subgroups that are still in draft, this makes the application throw an error
-  Define Study -> Study Activities: 502 error appearing several times when add new study activity (Temporary fix applied).
-  Define Study -> Study Criteria: Cannot change rows per page for criteria's
-  Define Study -> Study Criteria: When filling in any template some codelists have Empty 'codes' 
-  Define Study -> Study Criteria: Units showing in lower case in inclusion Criteria
-  Define Study -> Study Criteria: Filtering selection fields showing long HTML scripted text format of 'Guidance text'
-  Define Study -> Study Purpose: Difference in objective/endpoint from define to view spec to download
-  Define Study -> Study Purpose: Endpoint titles come with HTML when using a filter
-  Define Study -> Study Purpose: Previous selection does not disappear after importing a template
-  Define Study -> Study Purpose: Duplicated template parameters found in the Study Endpoint section.   
-  Define Study -> Study Structure: In Study Elements only 10 elements are shown even though more elements have been created
-  Define Study -> Study Structure: This page is not functional if a "Special Visit"  incorrectly is the only visit in a "Study Epoch" 
-  Define Study -> Study Structure: Week selected as preferred time unit is not reflected in Protocol SoA
-  Define Study -> StudySoAFootnotes is automatically updated when FootnotesRoot is updated, API returning latest FootnotesValue
-  View Listings -> Analysis study Metadata(New):  Page displays "white page" on Analysis Study Metadata page
-  View Specification -> SDTM Study Design Datasets: Excel download replace Null value by None - Should stay as empty cells


##  V 0.7.3 (01-FEB-2024)

## Fixes and Enhancements

### Studies
- Unwanted HTML tags are removed when listing 'Study Endpoint' template parameter values for selection in e.g. Study Objectives of Study Purpose.
- In the Version history table for various study elements, HTML characters in the text columns have been removed in Study Criteria.
- SDTM study design datasets can now be downloaded without error.
- Hiding retired activities and showing only Final activities in the list by default for better view in 'Studies' Module.

### Libraries
- Out of Memory error issue resolved when comparing the first and last version of a SDTM CT package in codelists.
- Removing "ADaM parameter code" as a mandatory field when adding a new Activitiy instance under concepts.
- If you hide a parameter in a sequence of parameters, the sentence generation is in correct format going forward for all template categories under Syntax templates.
- Hiding retired activities and showing only Final activities in the list by default for better view in 'Library' Module.
- On the "Overview" pages of "Activities" and "Activities Instances" boolean values are now displayed properly on the OSB YAML pane.
- Downloaded (.csv file) version of Inclusion Criteria Pre-instances contains all information going forward.

### API
- Refactoring parts of the API code, including reduction of the number of calls made by the backend to the DataBase, to improve loading times when working with syntax templates.
- The fundamental fix on API query parameter 'at_specified_date_time'is implemented resulted with no errors in API endpoints going forward.

##  V 0.7.2 (28-NOV-2023)

### Fixes and Enhancements
- Physical data model updates made for relationships from ActivityItemClass via ActivityItems to CTTerms for each ActivityInstnance, including simplifying the relationship cardinality. Name attribute removed from ActivityItem node, and ActivityItem node is no longer individually versioned in root/value pairs, but versioned as part of the outbound relationship from ActivityInstanceValue nodes..
- Study activity selection support selection of a specific activity grouping combination. Support the same activity can be added to the study activities multiple times under different groupings. Ability to display/hide groups for specific Activity Group combination. Ability to add SoA footnote at Activity Group level for specific group combination. Data collection Boolean added when searching and selection activities. Filtering corrected when searching and selection activities.is not working yet.
- New tabs added under Library -> Concepts -> Activities to support to support definition of activity groups and subgroups.Definition of activities and activity instances updated to use new activity groupings. Exiting tab for Activities by Groping now only support a hierarchal display of activity groupings. Page/size numbering is corrected when displaying activities in multiple groups. Data collection Boolean added for activities. NCI concept ID added for activities, activity instances and activity item class. Filtering and other display issues are corrected.
- Deleting a study epoch now reorders the remaining epochs correctly.
- The content on the Study Epoch page now remains visible after loading the Study Epochs page
- Adding a new visit more than once is now possible without reloading the Study Visit page under Study Structure.
- Proper error handling of strings with unbalanced parenthesis in Syntax Templates has been implemented in the API.
- API patching has been implemented for activityitemclass, if more than one version exists.
- Users are now able to select multiple study endpoints for secondary objectives under Study Purpose.
- The search bar on the Study Endpoints under Study Purpose is now working as intended.
- Indexes and constraints added to the database to improve query performance. This reduces loading times for the various pages related to syntax templates in the front-end.


### Other Changes

- StudyBuilder now supports creation and maintenance of footnotes in the Protocol SoA.

##  V 0.6.1 (27-SEP-2023)

### Fixes and Enhancements
- Syntax template refactorting includes 
    - Audit trial settings
    - API endpoints to retrieve Acitivity template instances
    - UI/UX improvements for study selections of syntax templates under study criteria
    - Study purpose and study activities, refinement of sequence numbering
    - Updates to 'edit' function for Objectives and Criterias
    - A number of improvements to both parent and pre-instance templates including display of history on both row and page level.

- Support multiple groupings and sub-groupings can be defined for activity concepts for both studies and libraries.

### New Features
- Under Study Activities sections, menu items and breadcrumbs where 'Flowchart' renamed to 'SoA' (Schedule of Activities), 'List of Study activities'renamed to 'Study Activities', 'Detailed Flowchart' renamed to 'Detailed SoA' and 'Protocol flowchart' renamed to 'Protocol SoA' in accordance with TransCelerate Common Protocol Template and ICH M11 terminology.
- SoA Footnotes implemented under Activities tab for Studies Module which helps the user can decide if the Activity Group or Subgroup is to be displayed or hidden in the Protocol SoA.

### Technical updates
- Renaming of 'data-import' repository to 'studybuilder-import'
- DDF adaptor repo changes from 'DDF-translator-lib' to 'studybuilder-ddf-api-adaptor'
- Neo4j DB version upgrade from V.4.4 to V.5.10, which includes Cypher changes (new syntax updates) and Management changes (changes to neo4j-admin, new command options, new backup file format and Custom procedures declaration updates). The versions precisely as neo4j DB version 5.10.0 and APOC version 5.10.1.

##  V 0.5 (05-JUL-2023)

### Fixes and Enhancements
- Improvements to audit trail tracking changes in outbound relationships to related nodes as changes.
- Documentation regarding packaging of python components (e.g. API) is outdated in several places. Corrected API issues reported by schemathesis. Auto-increment of version number enabled in the auto-generated openapi.json API specification.
Upgrade to Python version 3.11.
- Adding missing 'Number of Studies' column for Timeframe instance.
- Some column displays for activity instances has been removed, they will for the moment only be part of detailed displays.
- Improvements to license and SBOM display on About page.
- Various UI, Audit trail and Stability improvements.
- Syntax template functionalities in Library is refactored with improved data model and consistency.

### New Features
- System documentation and Online help on Locking and Versioning of Studies improved.
- Initial implementation for display of Data Exchange Standards for SDTM in Library menu (Part of the foundational data model representation linked to the Activity Concepts model similar to the CDISC Bio-medical Concepts mode).
- Import of core SDTM and SDTMIG data models from CDISC Library is supported going forward.
- New pre-instantiations of syntax templates replacing previous default values.
- Create and Maintain ClinSpark CRF Library using StudyBuilder
- Two sample study Metadata (MD) listings implemented to support ADaM dataset generation.

## V 0.4 (24-APR-2023)

### Fixes and Enhancements
- UI/UX improvements.
- Activity Placeholder updates and its corresponded API, UI, Logical and Physical data model updates.
- Sharing OpenStudyBuilder Solution code to Public gitlab (NN SBOM task file updates).
- Activity concepts model improvements, logical & physical data model updates.
- Enabling Study Metadata Listings, properties for generation of SDTM and relevant API endpoint updates.
- Improvements of CRF Management with vendor extension, CRF display in HTML or PDF format and OID & UID refactoring.
- Database Consistency Checks for Versioning Relationships on Library Nodes.
- Additional capabilities on Activity Instance and Item Class Model.
- Improved support for ODM.XML vendor extensions.
- Legacy migration of Activity Instance concepts have been adjusted to match the updated data model. Note the content is not fully curated yet, improvements will therefore come in next release.
- Global Audit Trail report shared as a NeoDash report (intially NeoDash report runs separately).

### New Features
- Locking and Versioning of Study Metadata (incl. API and UI Designs, Logical and Physical Data model updates).
- Import of core SDTM and SDTMIG data models from CDISC Library is supported now (Part of the foundational data model representation linked to the Activity Concepts model similar to the CDISC Bio-medical Concepts mode).
- The Data Model and Data Model IG data structures is extended with a number of attributes to support sponsor needs. Note the UI is not yet made for these part - sample data is loaded into the system database for utilisation by NeoDash reports.
- Initial version of DDF API adaptor enabling Digital Data Flow (DDF) compatible access to StudyBuilder as a DDF Study Definition Repository (SDR) solution.
- The data import repository will also include a DDF sample study. 
- The listing of activity concepts include links to overview pages of bot an Activity Concept and an Activity Instance Concept. This is on two separate tabs, one showing a form based overview and one showing a simplifies YAML based overview. The YAML based overview will in a later release be made fully CDISC COSMoS compliant.
- A NeoDash Report displayed with outbound relationships from the versioned value node.
- A NeoDash based report is included with a more comprehensive display and browsing capabilities of Activity Concepts. This NeoDash report in shared in the neo4j-mdr-db git repository and must be launched manually. 

## V 0.3 (17-FEB-2023)

### Fixes and Enhancements
- Fixes on CRF library
  - Issues on the Reference Extension on the Front-end fixed.
- Improvements on Study structure and Study Interventions.
- Fix applied on visual indication of required/mandatory (*) fields in UI so unnecessary error messages can be avoided.

### New Features
- Further additions to CRF library module.
- API refactoring done, majorly use of snake case and aligning SB API with Zalando Rest API guidelines.
- Implemented API to support Activity Placeholders and User Requested Activity Concept Requests.
- Audit trail history studies.
- Implemented Disease Milestones under Study Structure.
- OS packages has been added for generating PDF. OS software licenses are included in git repositories, including the third party licenses. 


## V 0.2 (12-DEC-2022)

### Fixes and Enhancements
- Locked version of documentation portal. 
- neo4j database version updated in dockerfile. 
- Updated README to correct default password error.
- Added README section about platform architectures and docker.
- Added separate README to allow for starting up the OpenStudyBuilder only using Docker for neo4j and the respective technologies for the rest of the components, such as python and yarn. This can be found in DeveloperSetupGuide.md.
- General source code quality improvements, below mentioned:
  - Aligned SB API with Zalando REST API Guidelines, e.g. naming of endpoints, query and path parameters, proper usage of HTTP methods etc.
  - A number of API refactorings to be more consistent in design and use of snake case including: Aligned StudyBuilder API with Zalando REST API Guidelines, e.g. naming of endpoints, query and path parameters, proper usage of HTTP methods etc.
  - Fixed major warnings reported by Pylint/SonarLint static code analyzers.
  - Removed unused endpoints and code.
- Filtering corrected for Activities in a number of places.
-  A number of fixes and improvements to CRF module:
  - Edit references from CRF tree.
  - Improvements in UI for CRF Instructions.
  - Support for exporting attributes as ODM.XML alias.
  - A number of corrections and improvements to the CRF Library pages and ODM.XML import and export capabilities
  - Improvements for ODM-XML Import.
  - API: Added a new field 'dispaly_text' on the relation between OdmItemRoot and CTTermRoot.
  - Data Model: Added 'display_text' between ODM Item and CT Term.
  - Mapper for ODM XML export added.
  - Added Import library for ClinSpark.
- A number of bug fixes including: 
   - All Study Field Selections related to CT must have relationships in the database to selected CT Term.
   - StudyBuilder is hanging when duplicating a StudyVisit is fixed.
   - All timings are available for syntax templates
- Improvements to sample data, data import and readme descriptions
- Improvements to SDTM Study Design dataset listings.
- Improvements on ease-of-use, clean and simplify sample data
- Page level Version History on Study Activities, Study Endpoints, Study Intervention, Registry identifier pages.
- Fix applied for Page level version history on Study Properties and on row level studies/criterias.

### New Features
- Flowchart fitting for studies with many visits.
- Improvements to Word add-in
- Support creation of special visits without a specific time point reference
- Support multiple ODM.XML styles and extensions.
- Initial implementation to support generation of Clinical Trial Registration information in CDISC CTR.XML format. Note this is in part one only available via the API, a display via the View Spcifications menu item will be added later. Study Objectives & Endpoints HTML table built in the UI.


## V 0.1 (24-OCT-2022)

Initial commit to Public Gitlab.