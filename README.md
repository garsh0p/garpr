Environment Setup
=================
1. Install mongodb
2. Start mongo: mongod &
3. Configure a user and a password for mongo against the admin database. (instructions here: http://docs.mongodb.org/manual/tutorial/add-admin-user/)
4. virtualenv env
5. source env/bin/activate
6. pip install -r requirements.txt (make sure to install the right version of mongomock as mentioned below)
7. Copy config/config.ini.template to config/config.ini and fill it out with a valid database/challonge config (the facebook section is not needed for tests and can be left with the dummy config). You'll need to change host to 127.0.0.1, then user and password to the username/password you setup in step #1. Set auth_db to 'admin' unless you did something different in step 3.

Versions issues
===============
mongomock was installed from master, not 2.0.0

    pip install git+https://github.com/vmalloc/mongomock.git@master

Importing Data
==============
Replace `garpr_db_dump_folder` with the path of the folder where the dump is stored. LIkewise, replace `admin` and `password` with the user and password you configured against your admin database.

	mongorestore garpr_db_dump_folder -u admin -p password

Running the API server
======================
This runs the server locally on port 3000 with the debug flag set

    python server.py 3000 True

Running the Angular app
=======================
Start a simple http server serving the pages in the `webapp` folder

	pushd webapp; python -m SimpleHTTPServer; popd

You probably want to change the `hostname` variable in `webapp/script.js` and set it to your local api server. It should look something like this.

	if (dev) {
	    var hostname = 'localhost:3000';
	}
	else {
	    var hostname = 'localhost:3000';
	}

Browse to localhost:8000 to view the application.

Local Development Using Vagrant
=======================
### Requirements
1. [Vagrant](https://www.vagrantup.com/downloads.html)
2. [VirturalBox](https://www.virtualbox.org/wiki/Downloads)
3. 1024 MB of memory

### Setup Steps
1. Clone the repository
	```
	git clone https://github.com/yedi/garpr.git
	```

2. Navigate to the project directory
	```
	cd garpr
	```

3. Run the Vagrantfile to setup the environment
	```
	vagrant up
	```

4. SSH into the development VM
	```
	vagrant ssh
	```

### Use
The vagrant user home directory of the VM will mirror the project directory on the host. It will also contain the project's dependencies.

To start the server run 
	```
	bash start.sh
	```

The API and webapp will now be started on the VM, and the webapp can be visited on the host @ 192.168.33.10:8000

To pull in any changes made to the project on the host into the VM, use the command `sync_vm`. This will allow you to use the text/project editors on your host.

1. (Host): Make edits to some files..
2. (VM): Run the command: `sync_vm`
3. (VM): Restart the system
4. (Host): Vist 192.168.33.10:8000 to view the new changes