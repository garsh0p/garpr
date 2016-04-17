#!/bin/bash
# General setup script

set -e # Exit script immediately on first error.

echo "Updating..."
sudo apt-get update

echo "Installing GIT..."
sudo apt-get install -y git

echo "Installing Python tools..."
sudo apt-get install -y python-dev libxml2-dev libxslt1-dev zlib1g-dev python-virtualenv

echo "rsyncing default Vagrant synced folder to vagrant user home..."
rsync -a /vagrant/ /home/vagrant