FROM python:3
ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /usr/local/lib/python3.7

ENV DEBUG=False
ENV HTTP_HOST=localhost
ENV DB_NAME=postgres
ENV DB_USER=postgres
ENV DB_HOST=db
ENV DB_PORT=5432
ENV DB_PASS=somepass
ENV ADMIN_PATH=b72c0824
ENV DO_MIGRATE=False

RUN apt-get update && apt-get -y install nginx
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
RUN rm /etc/nginx/sites-enabled/default
RUN mkdir -p /var/run/uwsgi && chown www-data:www-data /var/run/uwsgi
RUN mkdir -p /var/log/django && chown www-data:www-data /var/log/django && chmod g+s /var/log/django
COPY conf/cegov_nginx.conf /etc/nginx/sites-enabled/
COPY conf/uwsgi_params /etc/nginx/sites-enabled/
COPY conf/uwsgi.ini /etc/uwsgi.ini
COPY manage.py /code/
COPY bin/run-tests.sh /code/bin/run-tests.sh
COPY bin/run-server.sh /code/bin/run-server.sh
COPY ced /code/ced/
COPY api /code/api/
COPY govtrack /code/govtrack/
COPY static /code/static/
EXPOSE 8000
CMD [ "bin/run-server.sh" ]
