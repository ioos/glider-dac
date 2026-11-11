Feature: Glider Deployment Operations
      Tests related to various manipulations on glider deployments such as creation, deletion, or modification of the deployments.

     Scenario: Creation of new glider deployment
          Given I am a logged in user
          When I create a new glider deployment
          Then the requisite folder hierarchy should be created in the submission folder
          And an email should be sent notifying Glider DAC administrators of the new deployment

     Scenario: Deletion of glider deployment
          Given I am a logged in user
          When I create a new glider deployment
          And I attempt to delete an existing deployment belonging to my user
          Then the requisite folder hierarchy and any folders should be removed from the submission, ERDDAP, and THREDDS locations
          And the deployment should be deleted and no longer visible on any deployment page

    Scenario Outline: Reject unauthorized deployment mutations
        Given I am a logged in user
        When I create a new glider deployment
        Given I access the deployment as an "<actor>"
        When I post to the deployment "<operation>" endpoint using the "<url_user>" username
        Then the deployment request should return 403 without changing the deployment

        Examples:
            | actor          | operation     | url_user |
            | other user     | edit          | owner    |
            | other user     | edit          | caller   |
            | other user     | delete        | owner    |
            | other user     | delete        | caller   |
            | other user     | files         | owner    |
            | other user     | files         | caller   |
            | other user     | delete_files  | owner    |
            | other user     | delete_files  | caller   |
            | other user     | new real-time | owner    |
            | other user     | new delayed   | owner    |
            | inactive admin | edit          | owner    |
            | inactive admin | delete        | owner    |
            | inactive admin | files         | owner    |
            | inactive admin | delete_files  | owner    |
            | inactive admin | new real-time | owner    |
            | inactive admin | new real-time | caller   |
            | inactive admin | new delayed   | owner    |
            | inactive admin | new delayed   | caller   |
            | admin          | edit          | caller   |
            | admin          | delete        | caller   |
            | admin          | files         | caller   |
            | admin          | delete_files  | caller   |

    Scenario Outline: Allow owners and administrators to manage deployments
        Given I am a logged in user
        When I create a new glider deployment
        Given I access the deployment as an "<actor>"
        Then the deployment controls should use the owner's username
        When I post to the deployment "<operation>" endpoint using the "owner" username
        Then the deployment operation should succeed

        Examples:
            | actor | operation     |
            | owner | edit          |
            | owner | delete        |
            | owner | files         |
            | owner | delete_files  |
            | owner | new real-time |
            | owner | new delayed   |
            | admin | edit          |
            | admin | delete        |
            | admin | files         |
            | admin | delete_files  |
            | admin | new real-time |
            | admin | new delayed   |

    Scenario Outline: Allow users to create deployments under their own username
        Given I am a logged in user
        When I create a new glider deployment
        Given I access the deployment as an "<actor>"
        When I post to the deployment "<operation>" endpoint using the "caller" username
        Then the deployment operation should succeed

        Examples:
            | actor      | operation     |
            | other user | new real-time |
            | other user | new delayed   |
            | admin      | new real-time |
            | admin      | new delayed   |

    Scenario Outline: Missing deployments return not found
        Given I am a logged in user
        When I post to the missing deployment "<operation>" endpoint
        Then the deployment request should return 404

        Examples:
            | operation    |
            | edit         |
            | delete       |
            | files        |
            | delete_files |
            | new delayed  |

     Scenario: NCEI archival of deployments
          Given I am a logged in user
          When I create a new glider deployment
          And the deployment has been marked as completed and ready for NCEI archival
          And the deployment directory has one or more valid glider NetCDF files
          And the deployment exists in ERDDAP
          And the IOOS Compliance Checker has run the CF compliance checks against the deployment aggregation in ERDDAP
          And the single aggregated file exists in a folder with the NetCDF data
          Then the NCEI archival script will link the aggregated deployment file to the archival directory

    Scenario: Filtering deployments by name, WMO ID, and username
        Given there are deployments with different names, WMO IDs, and usernames
        When I filter deployments by name "kraken"
        Then only deployments with "kraken" in the name should be shown
        When I filter deployments by WMO ID "12345"
        Then only deployments with WMO ID "12345" should be shown
        When I filter deployments by username "miskatonic"
        Then only deployments with username "miskatonic" should be shown

    Scenario: Update user profile without changing password
        Given I am a logged in user
        When I update my user profile leaving password blank
        And I log out
        Then I should still be able to log in with original password
        And my updated name and email should be saved
