FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY manage.py /code/
COPY bin/run-tests.sh /code/bin/run-tests.sh
COPY bin/run-server.sh /code/bin/run-server.sh
COPY ced /code/ced/
COPY govtrack /code/govtrack/
EXPOSE 8000
CMD [ "bin/run-server.sh" ]
