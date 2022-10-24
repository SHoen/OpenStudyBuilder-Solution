Feature: ODMs Item Groups API

    As a Standards Developer,

    I want to create and maintain ODM Item Groups in the library, and relate them to our
    data concepts,

    So that they can be used consistently across studies, ensuring consistent mapping to Operational Data Model (ODM)
    and the Standards Data Tabulation Model (STDM) and its Implementation guide (STDMIG)


    Background: User is authenticated as Standards Developer
        Given Authentication token of 'Standards Developer' is obtained

    Scenario: Return a listing of ODM Item Groups
        Given ODM Item Groups exist
        When a 'GET' request is sent to 'concepts/odms/item-groups'
        Then a response with json body is received with the ODM Item Groups
        And the response has status code '200'

    Scenario: Return a listing of possible values for a given header
        Given ODM Item Groups exist
        When a 'GET' request is sent to 'concepts/odms/item-groups/headers?fieldName=name'
        Then a response with json body is received with the header values
        And the response has status code '200'

    Scenario: Return a specific ODM Item Group
        Given the ODM Item Group exists
        When a 'GET' request is sent to 'concepts/odms/item-groups/OdmItemGroup_000001'
        Then a response with json body is received with the specific ODM Item Group
        And the response has status code '200'

    Scenario: Return a listing of versions of a specific ODM Item Group
        Given the ODM Item Group exists
        When a 'GET' request is sent to 'concepts/odms/item-groups/OdmItemGroup_000001/versions'
        Then a response with json body is received with the versions of the specific ODM Item Group
        And the response has status code '200'

    Scenario: Create a new Item Group
        Given a Library exists
        And an Odm Description exists
        When a 'POST' request is sent to 'concepts/odms/item-groups' with
            """
            {
                "libraryName": "Sponsor",
                "oid": "G.DM.IC",
                "name": "Informed Consent",
                "repeating": "no",
                "isReferenceData": "no",
                "sasDatasetName": "DEMOG",
                "domain": "DS",
                "origin": "CRF",
                "purpose": "",
                "comment": "",
                "descriptionEngUid": "odm_description1"
            }
            """
        Then a response with json body is received containing
            """
            {
                "oid": "G.DM.IC",
                "name": "Informed Consent"
            }
            """
        And the response has status code '201'

    Scenario: Update an ODM Item Group
        Given the ODM Item Group is in 'Draft' status
        When a 'PATCH' request is sent to 'concepts/odms/item-groups/OdmItemGroup_000001' with
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

    Scenario: Delete an ODM Item Group
        Given the ODM Item Group exists
        When a 'DELETE' request is sent to 'concepts/odms/item-groups/OdmItemGroup_000001'
        Then a response with empty body is received
        And the response has status code '204'

    Scenario: Approving an Item Group
        Given the ODM Item Group is in 'Draft' status
        When a 'POST' request is sent to 'concepts/odms/item-groups/OdmItemGroup_000001/approve'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Inactivate an ODM Item Group
        Given the ODM Item Group is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/item-groups/OdmItemGroup_000001/inactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Retired"
            }
            """
        And the response has status code '201'

    Scenario: Reactivate an ODM Item Group
        Given the ODM Item Group is in 'Retired' status
        When a 'POST' request is sent to 'concepts/odms/item-groups/OdmItemGroup_000001/reactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Create a new version of an ODM Item Group
        Given the ODM Item Group is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/item-groups/OdmItemGroup_000001/new-version'
        Then a response with json body is received with the newly created version of the ODM Item Group
        And the response has status code '201'

    Scenario: Add ODM Items to an ODM Item Group
        Given the ODM Item Group exists
        And the ODM Items exist
        When a 'POST' request is sent to 'concepts/odms/item-groups/OdmItemGroup_000001/add-item-groups' with
            """
            [
                {
                    "uid": "OdmItem_000001",
                    "orderNumber": 1,
                    "mandatory": true,
                    "keySequence": "keySequence1",
                    "methodOid": "methodOid1",
                    "imputationMethodOid": "imputationMethodOid1",
                    "role": "role1",
                    "roleCodelistOid": "roleCodelistOid1",
                    "collectionExceptionConditionOid": "collectionExceptionConditionOid1"
                }
            ]
            """
        Then a response with json body is received with the ODM Item Group including the added ODM Items
        And the response has status code '201'

    Scenario: Remove ODM Items from an ODM Item Group
        Given the ODM Item Group exists
        When a 'POST' request is sent to 'concepts/odms/item-groups/OdmItemGroup_000001/remove-item-groups' with
            """
            {
                "items": [
                    "OdmItem_000001"
                ]
            }
            """
        Then a response with json body is received with the ODM Item Group without the removed ODM Items
        And the response has status code '201'

# # Following scenario has to be reviewed.
# Scenario: Linking the Item Group to the Activity and Sub-Activity
#     Given The activitiy exists in 'Final' status
#     When The 'POST' request is sent to '/odms/item-groups/{uid}' endpoint with JSON body containing activity IDs
#     Then The response with status code '201' is received
#     And The metadata for the updated Item Group is received

# # Following scenario has to be reviewed.
# Scenario: Linking the Item Group to the Model
#     Given The model exists in 'Final' status
#     When The 'POST' request is sent to '/odms/item-groups/{uid}' endpoint with JSON body containing model IDs
#     Then The response with status code '201' is received
#     And The metadata for the updated Item Group is received
