Feature: ODM Aliases API

    As a Standards Developer I want to create and maintain CRF Alias in the library, and relate them from the Forms, the Item Groups or Items.


    Scenario: Return a listing of ODM Aliases
        Given ODM Aliases exist
        When a 'GET' request is sent to 'concepts/odms/aliases'
        Then a response with json body is received with the ODM Aliases
        And the response has status code '200'

    Scenario: Return a listing of possible values for a given header
        Given ODM Aliases exist
        When a 'GET' request is sent to 'concepts/odms/aliases/headers?fieldName=name'
        Then a response with json body is received with the header values
        And the response has status code '200'

    Scenario: Return a listing of versions of a specific ODM Alias
        Given the ODM Alias exists
        When a 'GET' request is sent to 'concepts/odms/description/OdmAlias_000001/versions'
        Then a response with json body is received with the versions of the specific ODM Alias
        And the response has status code '200'

    Scenario: Create a new ODM Alias
        When a 'POST' request is sent to 'concepts/odms/aliases' with
            """
            {
                "name": "Domain",
                "context": "SDTM"
            }
            """
        Then a response with json body is received containing
            """
            {
                "name": "Domain",
                "context": "SDTM"
            }
            """
        And the response has status code '201'

    Scenario: Update an ODM Alias
        Given the ODM Alias exists
        When a 'PATCH' request is sent to 'concepts/odms/aliases/OdmAlias_000001' with
            """
            {
                "name": "Variable"
            }
            """
        Then a response with json body is received containing
            """
            {
                "name": "Variable"
            }
            """
        And the response has status code '200'

    Scenario: Delete an ODM Alias
        Given the ODM Alias exists
        When a 'DELETE' request is sent to 'concepts/odms/aliases/OdmAlias_000001'
        Then a response with empty body is received
        And the response has status code '204'

    Scenario: Approve an ODM Alias
        Given the ODM Alias is in 'Draft' status
        When a 'POST' request is sent to 'concepts/odms/description/OdmAlias_000001/approve'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Inactivate an ODM Alias
        Given the ODM Alias is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/aliases/OdmAlias_000001/inactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Retired"
            }
            """
        And the response has status code '201'

    Scenario: Reactivate an ODM Alias
        Given the ODM Alias is in 'Retired' status
        When a 'POST' request is sent to 'concepts/odms/aliases/OdmAlias_000001/reactivate'
        Then a response with json body is received containing
            """
            {
                "status": "Final"
            }
            """
        And the response has status code '201'

    Scenario: Create a new version of an ODM Alias
        Given the ODM Alias is in 'Final' status
        When a 'POST' request is sent to 'concepts/odms/description/OdmAlias_000001/new-version'
        Then a response with json body is received with the newly created version of the ODM Alias
        And the response has status code '201'