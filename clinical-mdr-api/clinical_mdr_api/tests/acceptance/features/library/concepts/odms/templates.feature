Feature: ODM Templates API

    As a Standards Developer,

    I want to create and maintain ODM Templates in the library, and relate them to our
    data concepts,

    So that they can be used consistently across studies, ensuring consistent mapping to Operational Data Model (ODM) and the Standards Data Tabulation Model (STDM) and its Implementation guide (STDMIG)


    Background: User is authenticated as Standards Developer
        Given Authentication token of 'Standards Developer' is obtained

    Scenario: Return a listing of ODM Templates
        Given ODM Templates exist
        When a 'GET' request is sent to 'concepts/odms/templates'
        Then a response with json body is received with the ODM Templates
        And the response has status code '200'

    Scenario: Return a listing of possible values for a given header
        Given ODM Templates exist
        When a 'GET' request is sent to 'concepts/odms/templates/headers?fieldName=name'
        Then a response with json body is received with the header values
        And the response has status code '200'

    Scenario: Return a specific ODM Template
        Given the ODM Template exists
        When a 'GET' request is sent to 'concepts/odms/templates/OdmTemplate_000001'
        Then a response with json body is received with the specific ODM Template
        And the response has status code '200'

    Scenario: Return a listing of versions of a specific ODM Template
        Given the ODM Template exists
        When a 'GET' request is sent to 'concepts/odms/templates/OdmTemplate_000001/versions'
        Then a response with json body is received with the versions of the specific ODM Template
        And the response has status code '200'

    Scenario: Create a new ODM Template
        Given a Library exists
        When a 'POST' request is sent to 'concepts/odms/templates' with
            """
            {
                "libraryName": "Sponsor",
                "name": "name1",
                "oid": "oid1",
                "effectiveDate": "effectiveDate1",
                "retiredDate": "retiredDate1",
                "formUids": []
            }
            """
        Then a response with json body is received containing
            """
            {
            "name": "name1",
            "oid": "oid1",
            "effectiveDate": "effectiveDate1",
            "retiredDate": "retiredDate1",
            }
            """
        And the response has status code '201'

    Scenario: Update an ODM Template
        Given the ODM Template is in 'Draft' status
        When a 'PATCH' request is sent to 'concepts/odms/templates/OdmTemplate_000001' with
            """
            {
                "oid": "new oid",
                "formUids": [],
                "changeDescription": "oid changed"
            }
            """
        Then a response with json body is received containing
            """
            {
                "oid": "new oid"
            }
            """
        And the response has status code '200'

    Scenario: Delete an ODM Template
        Given the ODM Template exists
        When a 'DELETE' request is sent to 'concepts/odms/templates/OdmTemplate_000001'
        Then a response with empty body is received
        And the response has status code '204'

    Scenario: Approve an ODM Template
        Given the ODM Template is in 'Draft' status
        When a 'POST' request is sent to 'concepts/odms/templates/OdmTemplate_000001/approve'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Inactivate an ODM Template
        Given the ODM Template is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/templates/OdmTemplate_000001/inactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Retired"
            }
            """
        And the response has status code '201'

    Scenario: Reactivate an ODM Template
        Given the ODM Template is in 'Retired' status
        When a 'POST' request is sent to 'concepts/odms/templates/OdmTemplate_000001/reactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Create a new version of an ODM Template
        Given the ODM Template is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/templates/OdmTemplate_000001/new-version'
        Then a response with json body is received with the newly created version of the ODM Template
        And the response has status code '201'