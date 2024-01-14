#!/usr/bin/env bash
rsync -a  --exclude='/data' . nebula@spica.uberspace.de:~/html/dev2.decarbnow.space
