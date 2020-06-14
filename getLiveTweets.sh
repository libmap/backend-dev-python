#!/usr/bin/env bash

if [ $# -eq 2 ]; then
    echo "Syncing, LIVE $1 -> LOCAL $2 ..."
    rsync -arv -e 'ssh -p 21022' decarbnow@decarbnow.abteil.org:/var/www/html/decarbnow/backend-dev-python/data/tweets/$1/ data/tweets/$2
else
    echo "Specify right count of args"
fi
