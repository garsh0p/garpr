#!/bin/bash
source config/config.ini

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
		python server.py $api_port True &
fi
if [[ "$(ps aux | grep SimpleHTTPServer)" == *"python -m SimpleHTTPServer"* ]]
	then
		echo "frontend is already running"
	else
		echo "starting frontend"
		pushd webapp; python -m SimpleHTTPServer $web_port; popd &
fi
echo "everything started, try http://localhost:$web_port"
