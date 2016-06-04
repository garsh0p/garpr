#!/bin/bash
if [ -z "$VIRTUAL_ENV" ] 
	then
		echo "activating venv"
		source ./env/bin/activate
	else
		echo "venv already active"
fi
if [[ "$(ps aux | grep mongo)" == *"mongod"* ]]
	then
		echo "mongod is already running"
	else
		echo "starting mongo"
		mongod &
fi
if [[ "$(ps aux | grep server.py)" == *"python server.py"* ]]
	then
		echo "backend is already running"
	else
		echo "starting backend"
		python server.py 3000 True &
fi
if [[ "$(ps aux | grep SimpleHTTPServer)" == *"python -m SimpleHTTPServer"* ]]
	then
		echo "frontend is already running"
	else
		echo "starting frontend"
		pushd webapp; python -m SimpleHTTPServer ; popd &
fi
echo "everything started, try http://localhost:8000"