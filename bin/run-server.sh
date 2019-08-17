#!/bin/bash

if [ "$DO_MIGRATE" == "True" ]
then
    python manage.py migrate
fi
if [[ -n "$HTTP_HOST" ]]
then
    echo "got http hosts: $HTTP_HOST"
    SERVER_NAMES=$(echo $HTTP_HOST | sed -e "s#,# #g")
    sed -i "s/HTTP_HOST/$SERVER_NAMES/" /etc/nginx/sites-enabled/cegov_nginx.conf
fi

service nginx start
uwsgi --ini /etc/uwsgi.ini

# this is awful but somehow the logs get created as root when uwsgi starts
# and are not writable by www-data otherwise
chown www-data /var/log/django/*log

tail -f /var/log/django/request.log

exit 0
