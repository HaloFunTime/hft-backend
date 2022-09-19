#!/bin/sh
CONTAINER_NAME="hftbackend"
if [ "$( docker container inspect -f '{{.State.Running}}' ${CONTAINER_NAME} 2>/dev/null )" == "true" ]
then
    echo "Running 'python manage.py ""$@""' in the ${CONTAINER_NAME} container..."
    docker exec -it ${CONTAINER_NAME} python manage.py ""$@""
else
    echo "Container ${CONTAINER_NAME} is not running. Try starting it by running dev-start.sh!"
fi
