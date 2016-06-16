#!/bin/bash
echo "assuming you don't want mongod killed"

if [[ -f "backend.pid" ]]
  then
    echo "shutting down backend"
    kill -9 $(cat "backend.pid")
    rm "backend.pid"
  else
    echo "backend is not running"
fi

if [[ -f "frontend.pid" ]]
  then
    echo "shutting down frontend"
    kill -9 $(cat "frontend.pid")
    rm "frontend.pid"
  else
    echo "frontend is not running"
fi
