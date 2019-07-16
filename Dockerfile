FROM python:3
ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code/
RUN pip install -r requirements.txt
COPY manage.py /code/
COPY ced /code/ced/
COPY govtrack /code/govtrack/
EXPOSE 8000
CMD [ "python", "manage.py", "runserver", "--insecure", "0.0.0.0:8000" ]
#CMD [ "tail", "-f", "/var/log/alternatives.log" ]
