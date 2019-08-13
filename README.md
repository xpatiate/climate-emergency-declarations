# climate-emergency-declarations

This repository is a work in progress, building a site that is intended to augment the current ICEF spreadsheet at https://bit.ly/ce-goverments

It's using Django with PostgreSQL to maintain a database tracking governments around the world which have recognised or declared a climate emergency.

It's currently under active development and will include:

* a public-facing front page which lists all government declarations of climate emergency
* a React frontend component on the front page, to allow filter/sort of declaration data
* admin tools to add and edit declarations
* logic to calculate overall population figures, incorporating special handling for governments at different hierarchical levels to avoid double-counting

## Running for local development and testing

When running in production, all environment variables set in `docker-compose.yml` are provided separately with secret managed values. For running a local dev copy, using the environment variables hardcoded into `docker-compose.yml` is fine. You can of course edit the environment variables if you prefer, just make sure they are consistent between the `db` and `web` services.

### Installation

The site can be run locally using Docker and Docker Compose. This will bring up two containers: a Postgres container for the database, and a Django container for the webserver. Here are the steps:

* Install [Docker](https://docs.docker.com/install/) and [Docker Compose](https://docs.docker.com/compose/install/)
* Clone this repository to your local system
* From the root directory of this repo, run `docker-compose -f docker-compose.yml up`
* You should now be able to access the site in a browser at http://127.0.0.1:8000/cegov/
* The code running within the web container is mapped from the local repo, so you can make changes to the code or templates and see them take effect immediately in the local site.

### Loading initial data

Run `bin/web-shell.sh` to open a shell in the web container. You can now interact with the Django `manage.py` script, e.g. `python manage.py check`

Load seed data into the database by running the following commands in the web container:
 * `python manage.py loaddata countries`
 * `python manage.py loaddata structures`
 * `python manage.py loaddata areas`

The "countries list" on your local site should now be populated.

Create an admin login with this command: `python manage.py createsuperuser`

Set a username and password here, then you can use these credentials to log in to the admin interface at http://127.0.0.1:8000/b72c0824/

Run `bin/db-shell.sh` to open a `psql` session to the local database.

### Testing

When docker-compose has both containers running, you can execute tests either from a shell in the web container: `python manage.py test`

or from a terminal on your local system, in the root directory of the repository: `./bin/run-container-test.sh`

Either way, this executes the Django test suite.

## Documentation links

* [Python](https://docs.python.org/3/)
* [Django](https://docs.djangoproject.com/en/2.2/)
* [Docker](https://docs.docker.com/)
* [PostgreSQL](https://www.postgresql.org/docs/11/index.html)
