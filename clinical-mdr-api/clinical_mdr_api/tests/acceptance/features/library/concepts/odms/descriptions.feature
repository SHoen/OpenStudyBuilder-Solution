Feature: ODM Descriptions API

    As a Standards Developer I want to create and maintain CRF Descriptions, Names and Instructions with language management in the library, and relate them from the Forms, the Item Groups or Items.


    Scenario: Return a listing of ODM Descriptions
        Given ODM Descriptions exist
        When a 'GET' request is sent to 'concepts/odms/descriptions'
        Then a response with json body is received with the ODM Descriptions
        And the response has status code '200'

    Scenario: Return a listing of possible values for a given header
        Given ODM Descriptions exist
        When a 'GET' request is sent to 'concepts/odms/descriptions/headers?fieldName=name'
        Then a response with json body is received with the header values
        And the response has status code '200'

    Scenario: Return a listing of versions of a specific ODM Description
        Given the ODM Description exists
        When a 'GET' request is sent to 'concepts/odms/descriptions/OdmDescription_000001/versions'
        Then a response with json body is received with the versions of the specific ODM Description
        And the response has status code '200'

    Scenario: Create a new ODM Description
        When a 'POST' request is sent to 'concepts/odms/descriptions' with
            """
            {
                "language": "ENG",
                "description": "Informed Consent and Demography form",
                "instruction": "Please do something"
            }
            """
        Then a response with json body is received containing
            """
            {
                "language": "ENG",
                "description": "Informed Consent and Demography form",
                "instruction": "Please do something"
            }
            """
        And the response has status code '201'

    Scenario: Update an ODM Description
        Given the ODM Description exists
        When a 'PATCH' request is sent to 'concepts/odms/descriptions/OdmDescription_000001' with
            """
            {
            "instruction": "Please complete this form",
            }
            """
        Then a response with json body is received containing
            """
            {
                "instruction": "Please complete this form"
            }
            """
        And the response has status code '200'

    Scenario: Delete an ODM Description
        Given the ODM Description exists
        When a 'DELETE' request is sent to 'concepts/odms/descriptions/OdmDescription_000001'
        Then a response with empty body is received
        And the response has status code '204'

    Scenario: Approve an ODM Description
        Given the ODM Description is in 'Draft' status
        When a 'POST' request is sent to 'concepts/odms/description/OdmDescription_000001/approve'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Inactivate an ODM Description
        Given the ODM Description is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/descriptions/OdmDescription_000001/inactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Retired"
            }
            """
        And the response has status code '201'

    Scenario: Reactivate an ODM Description
        Given the ODM Description is in 'Retired' status
        When a 'POST' request is sent to 'concepts/odms/descriptions/OdmDescription_000001/reactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Create a new version of an ODM Description
        Given the ODM Description is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/descriptions/OdmDescription_000001/new-version'
        Then a response with json body is received with the newly created version of the ODM Description
        And the response has status code '201'