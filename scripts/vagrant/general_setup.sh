#!/bin/bash
# General setup script
#   Brings in the project files

set -e # Exit script immediately on first error.

echo "Updating..."
sudo apt-get update

echo "Installing GIT..."
sudo apt-get install -y git

echo "rsyncing synced folder to vagrant user..."
rsync -a /vagrant/ /home/vagrant