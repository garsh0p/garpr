#!/bin/bash
# Project setup script

set -e # Exit script immediately on first error.

# echo "Creating/activating a Python virtual environment..."
virtualenv env
source env/bin/activate

echo "Installing project dependencies..."
pip install -r requirements.txt
pip install git+https://github.com/vmalloc/mongomock.git@master # use master instead of 2.0.0

# NOTE: if config/config.ini.template changes, this needs to change also
echo "Generating config file for development..." 
cat > ./config/config.ini <<'EOB'
[database]
host=127.0.0.1
auth_db=admin
user=devuser
password=devpass01

[challonge]
api_key=123temporaryKey1

[facebook]
app_id=123temporaryKey2
app_token=123temporaryToken1
EOB