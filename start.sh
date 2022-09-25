#! /usr/bin/bash

# this starts the gunicorn server and runs it as a daemon. It will log any app output into the script.out file. A tag has been added for easy process searching
nohup bash -c 'cd ./redis-api/ && exec -a redis-api python3 -m gunicorn redis-api:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8080 ' > ./script.out 2>&1 &

sleep 5s
# confirm all the processes are running
ps -aux | grep redis-api
