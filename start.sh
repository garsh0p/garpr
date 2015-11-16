#!/bin/bash
if [ -z "$VIRTUAL_ENV" ] 
	then
		source ./env/bin/activate
fi
python server.py 3000 True &
pushd webapp; python -m SimpleHTTPServer; popd