#!/bin/sh
if [ $# -eq 0 ]
then
    sh dev-manage.sh test apps
else
    APPS=()
    for arg in $@
    do
        APPS+=("apps/$arg")
    done
    sh dev-manage.sh test "${APPS[*]}"
fi
