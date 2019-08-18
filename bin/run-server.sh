#!/bin/bash

if [ "$DO_MIGRATE" == "True" ]
then
    python manage.py migrate
fi
if [[ -n "$HTTP_HOST" ]]
then
    SERVER_NAMES=$(echo $HTTP_HOST | sed -e "s#,# #g")
    sed -i "s/HTTP_HOST/$SERVER_NAMES/" /etc/nginx/sites-enabled/cegov_nginx.conf
fi

if [[ "$RUN_DEBUG_MODE" == "True" ]]
then
    service nginx stop
    python manage.py runserver  --insecure 0.0.0.0:8000
else
    service nginx start
    uwsgi --ini /etc/uwsgi.ini

    # this is awful but somehow the logs get created as root when uwsgi starts
    # and are not writable by www-data otherwise
    chown www-data /var/log/django/*log

    #tail -f /var/log/django/request.log
    tail -f /var/log/django/uwsgi.log
fi

exit 0
