---
title: Library Objectives Templates
date: 2020-11-26
tags:
  - objective
  - 203153
  - Library
---

# Objective Templates

> Feature: [Library of Sponsor Defined Objectives and Endpoints #169075](https://novonordiskit.visualstudio.com/Clinical-MDR/_workitems/edit/169075)<br/>
> User Story: [Create and Manage Objective Template #203159](https://novonordiskit.visualstudio.com/Clinical-MDR/_workitems/edit/203159)<br/>
> Enable: [API Endpoints/Objectives-templates #203153](https://novonordiskit.visualstudio.com/Clinical-MDR/_workitems/edit/203153)<br/>
> API Specification: [Objective Templates Endpoints](https://api.cmdr.novonordisk.com/docs#/Objective%20Templates)

This page is dedicated to the management of the *Objective Templates*. It will allow a **Standard Developer** to create and manage the *Objective Templates* needed to define the Objectives using Template Parameters (see the [Shared / objectives](./library/shared/objectives.md) submenu).

This concept of *Objective Templates* is illustrated in the figure 1 below. The Template Parameters are between [] and in blue. In the background, those Parameters are linked with some other metadata.

::: tip Definition

The objectives of a trial must be stated in specific terms. Achieving objectives should not depend on observing a particular outcome of the trial, e.g. finding a difference in mean weight loss of exactly 2 kg, but in obtaining a valid result. For example, a randomized trial of 4 diets had as its objective, “To assess adherence rates and the effectiveness of 4 popular diets for weight loss and cardiac risk factor reduction.” (Dansinger et al. 2005).

:::

![Objective Templates default page](~@source/images/library/standards/libraryObjectiveTemplate_Legends.png "Fig 1: Objective Templates default page")

The management of an Objective Template follow the versionning diagram below:

![Objective Templates Versionning](~@source/images/library/libraryElementsVersion_Workflow.png "Fig 2: Version Control of an Objective Templates")

## Add a new Objective Template

| Button | Behaviour       |
|:------:|:----------------|
| ![Add](~@source/images/bt_add_blue.png) | Click on the **'Add'** button. This will open a popup with an *Objective Template* form like below |

![Add an Objective Template](~@source/images/library/standards/popup_add_objectivestemplates.png "Fig 3: Add an Objective Template")

| Field | Definition       | Default Value | Mandatory |
| ------ |:---------------|:-------------:|:---------:|
| Library | Please select the library where you want to store your *Objective Template*. | Sponsor | Yes |
| Template | Complete this Textarea with the sentence of your *Objective Template*. Please note that as you are typing here, the system is suggesting some *Templates Parameters* that are linked with XXXXX. Those *Templates Parameters* after being selected from the below listing, will be surrounded by [] in the template text. | | Yes |
| Verify Syntax | After completing your Template, click here to verify if your *Objective Template* is using correct *Templates Parameters*. An Alert will be displayed with the result of the verification. | NA | |
| Cancel | Click here to close the popup windows WITHOUT saving your input. | NA | |
| Save | Click on this button to save your definition of your new *Objective Template* | NA | |

| Button | Behaviour       |
|:------:|:----------------|
| ![Verify Syntax](~@source/images/bt_verifysyntax_blue.png) | After completing your Template, click here to verify if your *Objective Template* is using correct *Templates Parameters*. An Alert will be displayed with the result of the verification. |
| ![Cancel](~@source/images/bt_cancel_blue.png) | Click here to close the popup windows WITHOUT saving your input. This will close the popup and display back the  |
| ![Save](~@source/images/bt_save_blue.png) | Click on this button to save your definition of your new *Objective Template* |

As soon as the newly created *Objective Template* is saved in the database, this new *Objective Template* will be added in the list of existing *Objectives Templates*. The added Objective Template will appear on the top of the table (based on the Last Modification Date).

And the popup will be closed. An alert message will inform the user that the *Objective Template* has been created.

## Modify an existing Objective Template

| Button | Behaviour       |
|:------:|:----------------|
| ![Search](~@source/images/bt_modify_blue.png) | Click on the **'Modify'** button at the end of the row that you want to update. Please note that this button is available only for *Objective Template* that are in 'Draft' status. Clicking on it will open a dedicated popup with the *Objective Template* in modification mode like below |

![Modify an Objective Template](~@source/images/library/standards/popup_modify_objectivestemplates.png "Fig 4: Modify an Objective Template")

| Field | Definition       | Default Value | Mandatory |
| ------ |:---------------|:-------------:|:---------:|
| **Library** | Please select the library where you want to store your *Objective Template*. | Sponsor | Yes |
| **Template** | In the Textarea, you will retrieve the sentence of your *Objective Template* as it is now. <br/><br/>If the *Objective Template* is in **Draft**:<br/>Then you can modify the textarea by adding text, parameter, by modifying text and parameter (deletion if possible). | | Yes |
| **Change description** | Provide here the reason of the modification made to the *Objective Template*. This reason for change will be store in the history field. | | Yes |

| Button | Behaviour       |
|:------:|:----------------|
| ![Verify Syntax](~@source/images/bt_verifysyntax_blue.png) | After completing your Template, click here to verify if your *Objective Template* is using correct *Templates Parameters*. An Alert will be displayed with the result of the verification. |
| ![Cancel](~@source/images/bt_cancel_blue.png) | Click here to close the popup windows WITHOUT saving your input. This will close the popup and display back the  |
| ![Save](~@source/images/bt_save_blue.png) | Click on this button to save your definition of your new *Objective Template*. This will update the *Objective Template* to the next sub-version number. For example, if your Draft *Objective Template* was in version 0.2, then it will turn into 0.3 and so on. |


## Validate an Objective Template

| Button | Behaviour       |
|:------:|:----------------|
| ![Set Status to Final](~@source/images/bt_validate_blue.png) | Click on the **'Set the status of this template to Final'** button at the end of the row that you want to validate. Please note that this button is available only for *Objective Template* that are in 'Draft' status. Clicking on it will update the status of the *Objective Template* to Final and the version number will be increased by 1 (Example going from 0.2 to 1.0). Additionally, all Objectives that reference the current version of the template will be updated to a new version. |

## Inactivate / Reactive an Objective Template

| Button | Behaviour       |
|:------:|:----------------|
| ![Inactivate](~@source/images/bt_inactivate_blue.png) | Click on the **'Inactivate this Template'** button at the end of the row that you want to deactivate. This is only availabel for *Objective Template* that are in Final status. This will change the status of the *Objective Template from Final to Retired. Please note that the Version Number will stay unchanged. |
| ![Reactivate](~@source/images/bt_reactivate_blue.png) | Click on the **'Reactivate this Template'** button at the end of the row that you want to restore a previously in-activated Final *Objective Template*. Please note that this button is available only for *Objective Template* that are in 'Retired' status. Clicking on it will update the status of the *Objective Template* to Final and the version number will return as it was previously (Example If the previous Final version was 2.0 then the reactivated Template version will be again 2.0) |

## Create a new version of the  Objective Template

| Button | Behaviour       |
|:------:|:----------------|
| ![New Version](~@source/images/bt_newversion_blue.png) | Click on the **'Create a new version'** button at the end of the row that you want to create a new version of the *Objective Template*. This will create a new *Objective Template* with a Draft status and the version will be increased by 0.1. |

## Export the list of Objectives Templates

| Button | Behaviour       |
|:------:|:----------------|
| ![Export](~@source/images/bt_export_blue.png) | Click on the **'Export'** button (before the Add button).<br/>This will open a dropdown menu with the following options: <ul align="left"><li>CSV</li><li>JSON</li><li>XML</li><li>EXCEL</li></ul><br/>Selecting one option will export the content of the table in the selected format. Please note that the export will ignore the filter if any.<br/><br/>The name of the file is: MDRSB_Library_ObjectiveTemplates_yyyymmdd.xxx with xxx = csv or json or xml or xlsx |

## View the Audit Trail of an Objective Template

| Button | Behaviour       |
|:------:|:----------------|
| ![History](~@source/images/bt_history_blue.png) | Click on the **'History'** button.This will open a new modal page like bellow:<br/>Please note that the history is sorted in  |

![Audit Trail Example](~@source/images/library/standards/library-standards-template-objective-history.png "Fig 5: Audit Trail Objective Templates example page")

## Search, Filter and Paginate

| Button | Behaviour       |
|:------:|:----------------|
| ![Search](~@source/images/bt_search_blue.png) | Click on the **'Search'** field. This will search in the *Objectives Templates* table based on the term of the seach.<br/><br/>In the search field, enter some words and automatically the table will be filtered based on it. You can filter also on status (look for Draft or Final), on version or on library. |
| ![Rows per page](~@source/images/bt_rows_blue.png) | You can also filter the number of record to be displayed in the table by changing the number of row per page (Select 5, 10, 15 or All).<br/><br/>This action will modify the pagination of the table. |
| ![Pagination buttons](~@source/images/bt_pagination_blue.png) | Based on the number of record displayed, the pagination of the table will display multiple pages. Click on the "<" or the ">" to navigate between pages.<br/><br/>We you are on the first or the last page then the symbol "<" or ">" will not be clickable anymore. | 
