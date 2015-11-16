#!/bin/bash
if [ -z "$VIRTUAL_ENV" ] 
	then
		echo "activating venv"
		source ./env/bin/activate
fi
if [[ "$(ps aux | grep server.py)" == *"python server.py"* ]]
	then
		echo "backend is already running"
	else
		python server.py 3000 True &
fi
if [[ "$(ps aux | grep SimpleHTTPServer)" == *"python -m SimpleHTTPServer"* ]]
	then
		echo "frontend is already running"
	else
		pushd webapp; python -m SimpleHTTPServer &; popd
echo "everything started, try http://localhost:8000"