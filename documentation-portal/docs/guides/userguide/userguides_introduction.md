# Introduction

This is the user guide of the MDR Study Builder application.
The solution is a combination of the following:
- A graph database - Here we are using Neo4j (in version 4.0)
- An API - We are using the Python FastAPI application
- A Frontend - The Vue.js + Vuetify system is been used

We have a central shared solution mostly dealing with a API.

[![Conceptual architecture for the clinical-MDR and the StudyBuilder](~@source/images/documentation/conceptual-architecture.png)](../../images/documentation/conceptual-architecture.png)

## Home page of the application

Please use the following URL to access the MDR Study Builder application:

    https://xxx.yyyyyy.zzz

![Study Builder](~@source/images/schema_02.png)

## User authentication

Before being able to fully work with the **Study Builder** you need to authenticate by providing a User and a Password information.

Use the following link to log in the application.

## After being authenticated

## Different User access

Based on the Roles & Permissions of the user, you can have access to different area of the tool.

## Navigation basics

Upon logging in, all navigation occurs within the same app. Navigating by using the browser arrows is possible, but not necessary, as the menus at the top and left of the screen allow simple, efficient navigartion throughout the whole application, regardless of the user's current location.

The primary menu at the top of the screen provides access to the modules **"Library"**, **"Studies"** and **"Workflows"**. Additionally, the user sees a settings button ![Settings](~@source/images/bt_settings_blue.png) and a help ![Help](~@source/images/bt_help_blue.png), which provide customization options and navigation support. The logout button is reachable upon clicking on the user name. 
By clicking the sandwich icon ![Sandwich](~@source/images/bt_sandwich_blue.png) the secondary navigation is hidden or shown.
The secondary navigation is located on the left-hand side and is distinct for each of the modules in the primary top menu.

![Navi](~@source/images/navi_overview.png)


## Legend of signs and symbols

| Button | Behaviour       |
|:------:|:----------------|
| ![Add](~@source/images/bt_add_blue.png) | **'Add'** button. Clicking on it will open a dialogue for creating new elements |
| ![Edit](~@source/images/bt_modify_blue.png) | Click on the **'Edit'** button to update existing elements. This will open a dedicated pop up with the selected element in modification mode |
| ![Set Status to Final](~@source/images/bt_validate_blue.png) | Click on the 'Set the status of this template to Final' button at the end of the row that you want to validate. This will update the status of the element to Final and the version number will be increased by 1. |
| ![Inactivate](~@source/images/bt_inactivate_blue.png) | Click on the **'Inactivate this Template'** button at the end of the row that you want to deactivate. |
| ![Reactivate](~@source/images/bt_reactivate_blue.png) | Click on the **'Reactivate this Template'** button at the end of the row that you want to in-activate. |
| ![New Version](~@source/images/bt_newversion_blue.png) | Click on the **'Create a new version'** button at the end of the row that you want to create a new version of the selected template. |
| ![Export](~@source/images/bt_export_blue.png) | Click on the **'Export'** button (before the Add button) to export the full set of *Objectives Templates*. |
| ![History](~@source/images/bt_history_blue.png) | Click on the **'History'** button.This will open a new modal page like bellow:<br/>Please note that the history is sorted in versioning order |
| ![Delete](~@source/images/bt_delete.png) | Click on the **'Delete'** button to remove an existing element. |
| ![Search](~@source/images/bt_search_blue.png) | Click on the **'Search'** field. This will search in the current templates table based on the term of the search. |
| ![Rows per page](~@source/images/bt_rows_blue.png) | You can also filter the number of record to be displayed in the table by changing the number of row per page. |
| ![Pagination buttons](~@source/images/bt_pagination_blue.png) | Based on the number of record displayed, the pagination of the table will display multiple pages. | 

## Versioning of each element

Each element in the MDR system is versioned automatically with its creation and has two attributes to support the process: 
- Status: Can be either **'Draft'**, **'Final'** or **'Retired'**. The status is changed manually upon verification of the element.
- Version: Is incremented manually upon adding a new template version from the **'Actions'** column


## Audit trail

Throughout the MDR application each entry made is documented in the audit trail.
The audit trail provides users with the appropriate permissions to view a table with the following information about each entry in the MDR system:

| Column name | Description |
|:------:|:----------------|
| Library |  |
| Template |  |
| Change description |  |
| Status |  |
| Version |  |
| User | containing the initials of the person who made the last modification |
| From | containing date and timepoint of the last modification |
| To |  |

## Working with the tables

In each module all activities are performed in tables.
Each table has general actions and such, which are module- or element-specific.
General actions are listed in the table ribbon:
[!Table Ribbon (/table_ribbon.png)]

The current export options include CSV, XML, JSON and Excel.




