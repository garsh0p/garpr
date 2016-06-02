#!/bin/bash
# General setup script

set -e # Exit script immediately on first error.

echo "Updating..."
sudo apt-get update

echo "Installing GIT..."
sudo apt-get install -y git

echo "Installing Python tools..."
sudo apt-get install -y python-dev python-pip libxml2-dev libxslt1-dev zlib1g-dev

echo "rsyncing default Vagrant synced folder to vagrant user home..."
rsync -a /vagrant/ /home/vagrant

# This will create an alias for running the rsync command
# to sync the project files in the VM with the files on the host
echo "alias sync_vm='rsync -r --delete --exclude=.* --exclude=env --exclude=config/config.ini /vagrant/ /home/vagrant'" >> ~/.bashrc