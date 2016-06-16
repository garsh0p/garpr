#!/bin/bash
# Project setup script

set -e # Exit script immediately on first error.

echo "Installing project dependencies..."
sudo pip install -r requirements.txt
sudo pip install git+https://github.com/vmalloc/mongomock.git@master # use master instead of 2.0.0

# NOTE: if config/config.ini.template changes, this needs to change also
#       the challonge api key is for a throw-away dev account
echo "Generating config file for development..."
cat > ./config/config.ini <<'EOB'
[environment]
name=dev
web_port=8000
api_port=3000

[database]
host=127.0.0.1
db=garpr
auth_db=admin
user=devuser
password=devpass01

[challonge]
api_key=H3rbHCGvVMjlZMo4CcaY3lMU6KS8kpfXN2I7arw8

[facebook]
app_id=123temporaryKey2
app_token=123temporaryToken1
EOB
