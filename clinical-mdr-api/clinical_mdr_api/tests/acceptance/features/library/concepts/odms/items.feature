Feature: ODM Items API

    As a Standards Developer,

    I want to create and maintain ODM Items in the library, and relate them to our
    data concepts,

    So that they can be used consistently across studies, ensuring consistent mapping to Operational Data Model (ODM) and the Standards Data Tabulation Model (STDM) and its Implementation guide (STDMIG)


    Background: User is authenticated as Standards Developer
        Given Authentication token of 'Standards Developer' is obtained

    Scenario: Return a listing of ODM Items
        Given ODM Items exist
        When a 'GET' request is sent to 'concepts/odms/items'
        Then a response with json body is received with the ODM Items
        And the response has status code '200'

    Scenario: Return a listing of possible values for a given header
        Given ODM Items exist
        When a 'GET' request is sent to 'concepts/odms/items/headers?fieldName=name'
        Then a response with json body is received with the header values
        And the response has status code '200'

    Scenario: Return a specific ODM Item
        Given the ODM Item exists
        When a 'GET' request is sent to 'concepts/odms/items/OdmItem_000001'
        Then a response with json body is received with the specific ODM Item
        And the response has status code '200'

    Scenario: Return a listing of versions of a specific ODM Item
        Given the ODM Item exists
        When a 'GET' request is sent to 'concepts/odms/items/OdmItem_000001/versions'
        Then a response with json body is received with the versions of the specific ODM Item
        And the response has status code '200'

    Scenario: Create a new ODM Item
        Given a Library exists
        And an ODM Description exists
        When a 'POST' request is sent to 'concepts/odms/items' with
            """
            {
                "libraryName": "Sponsor",
                "oid": "I.STUDYID",
                "name": "Study ID",
                "prompt": "",
                "datatype": "string",
                "length": "11",
                "significantDigits": "",
                "codelistRef": [],
                "measurementUnitRef": [],
                "sasFieldName": "STUDYID",
                "sdsVarName": "STUDYID",
                "origin": "PROTOCOL",
                "comment": "",
                "descriptionEngUid": "odm_description1",
                "descriptions": [],
                "aliases": [],
                "unitDefinitions": [],
                "activities": []
            }
            """
        Then a response with json body is received containing
            """
            {
                "oid": "I.STUDYID",
                "name": "Study ID"
            }
            """
        And the response has status code '201'

    Scenario: Update an ODM Item
        Given the ODM Item is in 'Draft' status
        When a 'PATCH' request is sent to 'concepts/odms/items/OdmItem_000001' with
            """
            {
                "comment": "new comment",
                "descriptionEngUid": "odm_description1",
                "descriptionUids": [],
                "aliasUids": [],
                "unitDefinitions": [],
                "changeDescription": "comment added"
            }
            """
        Then a response with json body is received containing
            """
            {
                "comment": "new comment"
            }
            """
        And the response has status code '200'

    Scenario: Delete an ODM Item
        Given the ODM Item exists
        When a 'DELETE' request is sent to 'concepts/odms/items/OdmItem_000001'
        Then a response with empty body is received
        And the response has status code '204'

    Scenario: Approve an ODM Item
        Given the ODM Item is in 'Draft' status
        When a 'POST' request is sent to 'concepts/odms/items/OdmItem_000001/approve'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Inactivate an ODM Item
        Given the ODM Item is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/items/OdmItem_000001/inactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Retired"
            }
            """
        And the response has status code '201'

    Scenario: Reactivate an ODM Item
        Given the ODM Item is in 'Retired' status
        When a 'POST' request is sent to 'concepts/odms/items/OdmItem_000001/reactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Create a new version of an ODM Item
        Given the ODM Item is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/items/OdmItem_000001/new-version'
        Then a response with json body is received with the newly created version of the ODM Item
        And the response has status code '201'

    Scenario: Add Activities to an ODM Item
        Given the ODM Item exists
        And the Activities exist
        When a 'POST' request is sent to 'concepts/odms/items/OdmItem_000001/add-activities' with
            """
            {
                "activities": [
                    "Activity_000001"
                ]
            }
            """
        Then a response with json body is received with the ODM Item including the added Activities
        And the response has status code '201'

    Scenario: Remove Activities from an ODM Item
        Given the ODM Item exists
        When a 'POST' request is sent to 'concepts/odms/items/OdmItem_000001/remove-activities' with
            """
            {
                "activities": [
                    "Activity_000001"
                ]
            }
            """
        Then a response with json body is received with the ODM Item without the removed Activities
        And the response has status code '201'