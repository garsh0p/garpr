#!/bin/bash
# MongoDB install script

set -e # Exit script immediately on first error.

echo "Installing MongoDB..."
sudo apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv EA312927
echo "deb http://repo.mongodb.org/apt/ubuntu trusty/mongodb-org/3.2 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-3.2.list
sudo apt-get update

# Installs mongo
sudo apt-get install -y mongodb-org

# Add development user
mongo admin --eval "db.createUser({user:'devuser',pwd:'devpass01',roles:[{role:'root',db:'admin'}]})"

# Turn on authentication (off by default)
echo '' | sudo tee --append /etc/mongod.conf
echo 'security:' | sudo tee --append /etc/mongod.conf
echo '  authorization: enabled' | sudo tee --append /etc/mongod.conf

sudo service mongod restart