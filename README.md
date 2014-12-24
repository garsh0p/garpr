Environment Setup
=================
1. Install mongodb
2. Configure a user and a password for mongo against the admin database.
3. virtualenv env
4. source env/bin/activate
5. pip install -r requirements.txt (make sure to install the right version of mongomock as mentioned below)
6. Copy config/config.ini.template to config/config.ini and fill it out with a valid database/challonge config (the facebook section is not needed for tests).

Versions issues
===============
mongomock was installed from master, not 2.0.0

    pip install git+https://github.com/vmalloc/mongomock.git@master

