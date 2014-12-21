Getting Started with garpr (windows)
====================================

This getting started is targeted at developers and people already somewhat familiar with interacting with the challonge api.

In this example, we will go through the process of setting up a mongodb database, importing tournament results from challonge, and generating rankings for your region.

To get started with garpr you need an installation of Python 2.7 and an installation of mongodb.

For mongodb, follow the installation guides and first steps located here: http://docs.mongodb.org/manual/

Once you have a mongodb instance up and running and you've create your first database (I suggest naming it 'meleedata' or something similar). You'll want to add a user with read-write permissions to this database (read this page and follow the steps: http://docs.mongodb.org/manual/core/authentication/)

Once you have a user, the next step is to setup a config.ini file. Go to garpr/config and grab the template file. Inside you'll find the fields shown below. Save this file as config.ini in the same folder and then modify the fields below as appropriate (you can get the mongodb host name by logging in with a mongod client and finding the appropriate command by calling "help" from the command line).

The authdb is your database in which your create user has permissions (i.e. "meleedata"). The rest of the fields are self explanatory. You don't need a facebook token if you're working on a local machine.

[database]
host=HOSTNAME
auth_db=AUTH_DB
user=USER
password=PASSWORD

[challonge]
api_key=API_KEY

[facebook]
app_id=FB_APP_ID
app_token=FB_APP_TOKEN

Once you have config setup, the next step is to initialise your database with a region. Grab the intialise_region script from the scripts directory and copy it into the main garpr directory. Run the script and enter values at the prompt.

The last step is to run the import_tournament script. Once again you need to copy this into the main garpr directory and run it from there. You will need the id of the tournament you wish to pull from challonge. This will soon be possible with the tournament url, but this feature has not been implemented yet. You can get this id by making an index call using any software (excel) capable of making an API call

These are the very bare first steps required to get started with a local database.


Versions issues
===============
mongomock was installed from master, not 2.0.0

    pip install git+https://github.com/vmalloc/mongomock.git@master
