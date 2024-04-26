Feature: Glider Deployment Operations
      Tests related to various manipulations on glider deployments such as creation, deletion, or modification of the deployments.

     Scenario: Creation of new glider deployment
          Given I am a logged in user
          When I create a new glider deployment 
          Then the requisite folder hierarchy should be created in the submission folder 
          And an email should be sent notifying Glider DAC administrators of the new deployment 

     Scenario: Deletion of glider deployment
          Given I am a logged in user or admin user
          When I attempt to delete an existing deployment belonging to my user 
          Then the requisite folder hierarchy and any folders should be removed from the submission, ERDDAP, and THREDDS locations
          And the deployment should be deleted and no longer visible on any deployment page 

     Scenario: NCEI archival of deployments
          Given a deployment has been marked as completed and ready for NCEI archival in the application by the user who created the deployment or an admin user
          When the deployment exists in ERDDAP
          And the IOOS Compliance Checker has run the CF compliance checks against the deployment aggregation in ERDDAP 
	  Then the NCEI archival script will link the aggregated deployment file to the archival directory
