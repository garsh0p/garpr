Environment Setup
=================
1. Install mongodb
2. Start mongo: mongod &
3. Configure a user and a password for mongo against the admin database. (instructions here: http://docs.mongodb.org/manual/tutorial/add-admin-user/)
4. virtualenv env
5. source env/bin/activate
6. pip install -r requirements.txt (make sure to install the right version of mongomock as mentioned below)
7. Copy config/config.ini.template to config/config.ini and fill it out with a valid database/challonge config (the facebook section is not needed for tests and can be left with the dummy config). You'll need to change host to 127.0.0.1, then user and password to the username/password you setup in step #1. You should be able to leave auth_db unchanged. 

Versions issues
===============
mongomock was installed from master, not 2.0.0

    pip install git+https://github.com/vmalloc/mongomock.git@master

