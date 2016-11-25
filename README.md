Welcome to GarPR Development

Our dev environment uses vagrant. 
We have a CI cycle, with a big test suite, and auto-push to
production based on jenkins when we push to master and pass all tests

garpr is written using Restful Flask on the backend, with an AngularJS frontend.

Developers should make changes in a branch, and then make a pull request (also see [here](https://github.com/ripgarpr/garpr/blob/master/jenkins/README.md)).

Admins or users, submit bug reports on the [issues page](https://github.com/ripgarpr/garpr/issues).

Interested in getting GarPR in your region? Contact one of the devs. 

Interested in being a dev? Also contact one of us. We have an active slack channel :D

Local Development Using Vagrant
==============================
### Requirements
1. [Vagrant](https://www.vagrantup.com/downloads.html)
2. [VirtualBox](https://www.virtualbox.org/wiki/Downloads)
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

3. Run the Vagrantfile to setup the environment. Note that if your Vagrant version is too old, you may get an error, so make sure you get the latest version from their website.
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

1. (Host): Make edits to some files.
2. (VM): Run the command: `sync_vm`
3. (VM): Restart the system (often the system will auto-restart; to force restart, type `bash stop.sh` followed by `bash start.sh`). 
4. (Host): Visit 192.168.33.10:8000 to view the new changes.

If stuff goes very wrong (or you would like to restore the initial copy of your db), you can restore the initial state of the Vagrant VM by typing `vagrant destroy` followed by `vagrant up`.

### Running tests
To run all tests:
  ```
  nosetests
  ```
