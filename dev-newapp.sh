#!/bin/sh
mkdir apps/$1
sh dev-manage.sh startapp $1 apps/$1
