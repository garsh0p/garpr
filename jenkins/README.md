Guide to deploying with Jenkins
===============================

To make continuous deployment easy, we've set up Jenkins on the production server. This file is a brief guide to how to deploy new versions of the code through Jenkins.

Overview
========

At any time, there should be two copies of GarPR running in separate environments on the production server. The first environment, the *stage* environment, is intended for testing the most recent build of GarPR. Any update to master on the github repo will cause Jenkins to update stage, run nosetests, and restart the stage environment. Currently the stage environment is accessible at https://www.notgarpr.com:8443 (with the api being served at https://www.notgarpr.com:3013). You can also access the stage environment at https://stage.notgarpr.com.

When you're convinced that the stage copy is working as intended, you can manually tell Jenkins to push the changes to the *prod* environment. This is the version of GarPR that all users will interact with. Currently the prod environment is accessible at https://www.notgarpr.com (with the API being served at https://www.notgarpr.com:3001).

Using Jenkins
=============

Starting builds through Slack
----------------------------

The recommended way to stage/deploy new builds is via Slack commands on our Slack channel. Typing "/stage <branchname>" anywhere in Slack will prompt Jenkins to run tests on and (if they succeed) stage branch <branchname> on the stage copy. Typing "/deploy" will deploy the most recent version of master that has successfully been staged to the prod copy. In particular, note that you should "/stage master" before you "/deploy". A typical workflow for deploying a feature should look as follows:

1. Open branch "featurename" for your new feature.
2. Code your feature in this branch.
3. When the feature is ready, push this branch to GH and open a PR for this feature.
4. Stage this branch on the staging copy by typing "/stage featurename". 
5. If step 4 is successful and the feature works fine on stage, merge your PR.
6. Stage the merged copy of master by typing "/stage master".
7. If the staged copy of master looks fine, deploy to prod by typing "/deploy".

Starting builds through Jenkins
-------------------------------

Currently the Jenkins web interface is being served at www.notgarpr.com:8080. You will need a username and password to log in: ask in Slack for the appropriate credentials.

There are currently two projects in Jenkins, "garpr_stage" and "garpr_prod", corresponding to updating the stage and prod environment. In a project, click "Build Now" on the left menu to manually trigger a build. You can see the currently active builds in the "Build Queue" on the left (or by clicking "Builds"). On the page for any given build, you can see whether it failed or succeeded, along with any console output it may have generated.

Backups
=======

Backups of the database are taken daily, are labeled by date (e.g. "2016-06-20.zip") and can be found at /home/deploy/dumps on the production server. For access, ask on Slack. (TODO: store backups somewhere else, e.g. AWS or Dropbox).

To manually take a backup, you can build the "backup" project in Jenkins (in much the same way as described above).
