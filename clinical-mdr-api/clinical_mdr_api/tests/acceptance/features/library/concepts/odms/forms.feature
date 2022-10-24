Feature: ODM Froms API

    As a Standards Developer,

    I want to create and maintain ODM Forms in the library, and relate them to our
    data concepts,

    So that they can be used consistently across studies, ensuring consistent mapping to Operational Data Model (ODM) and the Standards Data Tabulation Model (STDM) and its Implementation guide (STDMIG)


    Background: User is authenticated as Standards Developer
        Given Authentication token of 'Standards Developer' is obtained

    Scenario: Return a listing of ODM Forms
        Given ODM Forms exist
        When a 'GET' request is sent to 'concepts/odms/forms'
        Then a response with json body is received with the ODM Forms
        And the response has status code '200'

    Scenario: Return a listing of possible values for a given header
        Given ODM Forms exist
        When a 'GET' request is sent to 'concepts/odms/forms/headers?fieldName=name'
        Then a response with json body is received with the header values
        And the response has status code '200'

    Scenario: Return a specific ODM Form
        Given the ODM Form exists
        When a 'GET' request is sent to 'concepts/odms/forms/OdmForm_000001'
        Then a response with json body is received with the specific ODM Form
        And the response has status code '200'

    Scenario: Return a listing of versions of a specific ODM Form
        Given the ODM Form exists
        When a 'GET' request is sent to 'concepts/odms/forms/OdmForm_000001/versions'
        Then a response with json body is received with the versions of the specific ODM Form
        And the response has status code '200'

    Scenario: Create a new ODM Form
        Given a Library exists
        And an ODM Description exists
        When a 'POST' request is sent to 'concepts/odms/forms' with
            """
            {
                "libraryName": "Sponsor",
                "name": "Vital Signs",
                "oid": "F.VS",
                "repeating": "no",
                "descriptionEngUid": "odm_description1"
            }
            """
        Then a response with json body is received containing
            """
            {
                "name": "Vital Signs",
                "oid": "F.VS"
            }
            """
        And the response has status code '201'

    Scenario: Update an ODM Form
        Given the ODM Form is in 'Draft' status
        When a 'PATCH' request is sent to 'concepts/odms/forms/OdmForm_000001' with
            """
            {
                "repeating": "yes",
                "descriptionEngUid": "odm_description1",
                "changeDescription": "repeating changed to yes",
                "descriptionUids": []
            }
            """
        Then a response with json body is received containing
            """
            {
                "repeating": "yes"
            }
            """
        And the response has status code '200'

    Scenario: Delete an ODM Form
        Given the ODM Form exists
        When a 'DELETE' request is sent to 'concepts/odms/forms/OdmForm_000002'
        Then a response with empty body is received
        And the response has status code '204'

    Scenario: Approve an ODM Form
        Given the ODM Form is in 'Draft' status
        When a 'POST' request is sent to 'concepts/odms/forms/OdmForm_000001/approve'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Inactivate an ODM Form
        Given the ODM Form is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/forms/OdmForm_000001/inactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Retired"
            }
            """
        And the response has status code '201'

    Scenario: Reactivate an ODM Form
        Given the ODM Form is in 'Retired' status
        When a 'POST' request is sent to 'concepts/odms/forms/OdmForm_000001/reactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Create a new version of an ODM Form
        Given the ODM Form is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/forms/OdmForm_000001/new-version'
        Then a response with json body is received with the newly created version of the ODM Form
        And the response has status code '201'

    Scenario: Add Activity Groups to an ODM Form
        Given the ODM Form exists
        And the Activity Groups exist
        When a 'POST' request is sent to 'concepts/odms/forms/OdmForm_000001/add-activity-groups' with
            """
            {
                "activityGroups": ["ActivityGroup_000001"]
            }
            """
        Then a response with json body is received with the ODM Form including the added Activity Groups
        And the response has status code '201'

    Scenario: Remove Activity Groups from an ODM Form
        Given the ODM Form exists
        When a 'POST' request is sent to 'concepts/odms/forms/OdmForm_000001/remove-activity-groups' with
            """
            {
                "activityGroups": ["ActivityGroup_000001"]
            }
            """
        Then a response with json body is received with the ODM Form without the removed Activity Groups
        And the response has status code '201'

    Scenario: Add ODM Item Groups to an ODM Form
        Given the ODM Form exists
        And the ODM Item Groups exist
        When a 'POST' request is sent to 'concepts/odms/forms/OdmForm_000001/add-item-groups' with
            """
            [
                {
                    "uid": "OdmItemGroup_000001",
                    "orderNumber": 1,
                    "mandatory": true,
                    "collectionExceptionConditionOid": "collectionExceptionConditionOid1"
                }
            ]
            """
        Then a response with json body is received with the ODM Form including the added ODM Item Groups
        And the response has status code '201'

    Scenario: Remove ODM Item Groups from an ODM Form
        Given the ODM Form exists
        When a 'POST' request is sent to 'concepts/odms/forms/OdmForm_000001/remove-item-groups' with
            """
            {
                "itemGroups": ["OdmItemGroup_000001"]
            }
            """
        Then a response with json body is received with the ODM Form without the removed ODM Item Groups
        And the response has status code '201'