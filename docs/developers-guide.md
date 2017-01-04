Developer's Guide to GarPR
==========================

Introduction
------------

This document serves as a brief introduction to the overall structure of the
GarPR project for new developers. Some of the content of this guide will
undoubtedly be redundant for developers familiar with the DAO model and
writing webapps in Flask; for those developers we suggest just skimming the
index of descriptions of the main folders/files below.

The Webapp and the API
----------------------

The GarPR project consists of two web components running on different ports and
commmunicating via HTTP: the "webapp" component (alternatively, "frontend") and
the "API" component (alternatively, "backend"). The webapp component is written
primarily in HTML/Javascript (leveraging AngularJS) and is responsible for
serving HTML/JS files to the user. To get/modify data, the webapp component
interacts with the API component via Ajax queries.

The API component is written in Python, using the Flask web framework (http://flask.pocoo.org/)
The API is responsible for most of the core logic of the GarPR project. This
includes authenticating users, working with the database, computing rankings, etc.
The API component does not return any HTML, instead returning JSON data that the
frontend consumes. Currently, the API is being served over HTTPS on port 3001 of notgarpr.com.

Persistent data is stored in a MongoDB database. The API communicates with the database
via the pymongo library.

Subcomponents of the API
------------------------

The API primarily consists of three major subcomponents, each in their own Python file.
These subcomponents are the server, the DAO, and the models, stored in server.py,
dao.py, and model.py respectively.

The server (server.py) is the root Flask application. This is the file which directly
imports Flask and is run as a Flask app. This component is responsible for defining and
processing specific API URL endpoints.

The DAO (dao.py), short for "data access object" (https://en.wikipedia.org/wiki/Data_access_object),
forms the bridge between the server and the database. The DAO is responsible for querying
the database, packaging the received information, and sending it off to the server. As a
general design principle, as much data manipulation as possible should be done within the DAO;
the server should (for the most part) just receive a request, call the appropriate
DAO method, and return the output. The server should never query MongoDB directly;
this is the providence of the DAO.

The models (model.py) define the structure of the data stored in the database. Although
MongoDB is a schemaless database, most of the information we store does have a well-defined
structure. Each collection in MongoDB has a corresponding class in models.py, and queries to
this collection get converted to lists of objects of this class (via help of the ORM, which
we will discuss later).

The ORM
-------

The ORM (orm.py), short for Object-Relational Mapper, is responsible for handling
all conversions between external data (usually in the form of JSON) and Python objects
defined in model.py. This includes:

    - loading a JSON response by PyMongo into a native Python object.
    - loading a JSON response from the webapp to a native Python object.
    - serializing a native Python object into JSON in reply to a webapp request.
    - serializing a native Python object into JSON to be stored in MongoDB.

In addition to this, the ORM also performs run-time validation checks on data whenever
it is loaded or serialized (e.g., to ensure dates are actually dates, fields aren't empty,
etc.). It is possible to write custom validation rules for specific fields and documents.
For more information, consult the ORM guide (TODO: under construction).

Subcomponents of the Webapp
---------------------------

(TODO)

Index of Important Files and Directories
----------------------------------------

- config/: This directory contains configuration files for the API (configuration
variables for the webapp are stored in webapp/script-config.js). Technically, it is
also a Python module that is loaded by the API whenever a configuration variable is
required.
    - config.ini.template: template for configuration variables. In production this
    should be copied to config.ini and populated with the appropriate values.
    - config.py: Python script that loads and parses configuration variables from
    config.ini
    - dev-config.ini: This is the config.ini file for local development instances.
    On startup, Vagrant copies this file into config.ini.
- deploy/: This directory contains daemon scripts for keeping the webapp/api running,
even in the case of crashes/memory errors. Currently only the scripts in systemd/ are
run in production (the scripts in upstart/ are from when our server used to run Ubuntu 14.04).
These are only used on the production server (not in development in Vagrant).
    - systemd/: systemd (https://wiki.debian.org/systemd) scripts for keeping the web services
    up and running. There are four scripts for the four separate services: prod-api,
    prod-webapp, stage-api, and stage-webapp.
- dev/: This directory contains development-environment specific files that are not used
on the production server.
    - data/: This is the MongoDB dump that Vagrant uses to populate the development database.
    If you have a PR that involves migrating data/updating the DB schema, you should also update
    this dump or ask in Slack (ideally this will be taken care of automatically soon).
    - ssl/: This contains a self-signed certificate for the Vagrant IP (http://192.168.33.10/),
    used for testing SSL related stuff. The majority of the time you run GarPR in development,
    you shouldn't need this.
    - upstart/: This contains Upstart scripts for testing locally. If you would like to use these,
    copy them into /etc/init/, and run "start dev-api; start dev-webapp;". The majority of the time
    you run GarPR in development, you shouldn't need this (you should be running it directly from the
    command line via start.sh).
- jenkins/: This directory contains scripts used by the Jenkins automation server. For more
information, see the README.md file in jenkins/ or go to jenkins.notgarpr.com (ask on Slack
for creds).
- scraper/: This directory contains Python scripts responsible for scraping various sources
for tournament data. Right now we have three scrapers, for Challonge tournaments (challonge.py),
Tio tournaments (tio.py), and SmashGG tournaments (smashgg.py).
- scripts/: A miscellany of scripts that are (for the most part) run manually.
    - migrations/: This folder contains old DB migration scripts. If you write a PR that requires
    a DB migration, put a script in here and ask in Slack to run it on prod (there is a WIP
    to streamline this process so this isn't necessary).
    - old/: A bunch of old scripts. I don't know what many of them do, and certainly most
    won't run properly anymore.
    - vagrant/: These scripts are run by vagrant upon initialization.
    - take_backup.py: This script is run daily by Jenkins, and takes backups of the MongoDB
    database and stores them both locally on the server and in a Dropbox account.
    - validate_db.py: This script performs database-level validation on the data.
    It makes sure that all the data in mongodb is formatted correctly, that e.g.
    references in a Tournament document to Players refer to valid Player documents,
    etc. In some cases (if run with the '--fix' option), will also try to repair
    these issues. This script is also run daily by Jenkins.
- test/: Python unit tests. These can be run from the command line via
the nosetests command.
- webapp/: Root directory for the webapp component of GarPR. The contents of this
    directory are what are served to the user on the main URL.
    - app/: The main AngularJS application. This directory is organized into a
    variety of modules that are imported by app.js. Each of these modules contains
    the following subdirectories (see https://docs.angularjs.org/guide/concepts for
    an overview of what each of these concepts means in an AngularJS application):
        - controllers/: AngularJS controllers.
        - directives/: AngularJS directives.
        - services/: AngularJS services.
        - views/: AngularJS views.
        - something.module.js: declares this directory as an AngularJS module.
    - images/: Image files
    - lib/: Some JS libraries we serve locally (e.g. Angular and Bootstrap)
    - styles/: CSS stylesheets.
    - index.html: The root HTML file for the application.
    - script-config.js.template: Frontend configuration variables are stored in
    script-config.js. This file is a template for script-config.js.
    - dev-script-config.js: The script-config.js file for local dev instances.
    - serve_webapp.tac: This is a Twisted Application script for spawning the webapp
    on the server. See serve_api.tac for more details.
    On startup, Vagrant copies this into script-config.js.
- Vagrantfile: this tells Vagrant how to set up the virtual machine. It in turn
calls the scripts in /scripts/vagrant.
- start.sh: A bash script to start the application (webapp+api) in the local dev
environment. This runs under HTTP using a single process, and is only used for local
development. In production, the app is started via twisted using the Twisted
Application files  serve_api.tac and serve_webapp.tac.
- start_windows.sh: Same as start.sh, but works better on Vagrant boxes running
under Windows (start.sh can have issues for Windows users).
- stop.sh: A bash script to stop the application locally. Really, all it does is
kill all python processes. If you're not running this under Vagrant, be careful
when running this.
- serve_api.tac: Twisted Application file that spawns a Twisted service
(https://twistedmatrix.com/trac/) for the API. This is what the production server
uses to host the API, but you can also run this locally by running
`twistd -oy serve_api.tac`.
- ssl_util.py: A helper python script to deal with SSL certificates for serve_api.tac
and serve_webapp.tac.
- requirements.txt: Pip requirements file for the API backend.
- server.py: The root Flask application for the API backend. Handles API routes and
some other top-level Flask stuff.
