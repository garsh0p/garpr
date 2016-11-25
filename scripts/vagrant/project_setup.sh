#!/bin/bash
# Project setup script

set -e # Exit script immediately on first error.

echo "Installing project dependencies..."
sudo pip install -r requirements.txt

# NOTE: if config/config.ini.template changes, this needs to change also
#       the challonge api key is for a throw-away dev account
echo "Generating config file for development..."
cp ./config/dev-config.ini ./config/config.ini

echo "Generating javascript config file for development"
cp ./webapp/dev-script-config.js ./webapp/script-config.js
