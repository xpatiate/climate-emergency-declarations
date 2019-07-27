#!/bin/bash

if [ "$DO_MIGRATE" == "True" ]
then
    python manage.py migrate
fi
python manage.py runserver --insecure 0.0.0.0:8000

exit 0
