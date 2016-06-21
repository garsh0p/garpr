#!/bin/bash
set -e # Exit script immediately on first error.

if [[ "$(ps aux | grep mongo)" == *"mongod"* ]]
  then
    echo "mongod is already running"
  else
    echo "starting mongo"
    mongod &
fi
if [[ -f "backend.pid" ]]
  then
    echo "backend is already running"
  else
    echo "starting backend"
    twistd --pidfile="backend.pid" --logfile="backend.log" -oy serve_api.tac
fi
if [[ -f "frontend.pid" ]]
  then
    echo "frontend is already running"
  else
    echo "starting frontend"
    twistd --pidfile="frontend.pid" --logfile="frontend.log" -oy webapp/serve_webapp.tac
fi
echo "everything started"
