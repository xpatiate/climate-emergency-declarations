## Simple db backup scripts

Set up an EC2 t2.micro instance with a security group that allows it to connect to the live RDS.

Create a file with db connection parameters as follows, in the `ec2-user` home directory:
```
export DB_USER=postgres
export DB_PASS=
export DB_HOST=
export DB_NAME=

```

Create the following scripts in the `ec2-user` home directory
`dbclient.sh`:
```
docker run -it --rm jbergknoff/postgresql-client postgresql://$DB_USER:$DB_PASS@$DB_HOST:5432/$DB_NAME
```

`dbshell.sh`:
```
docker run -it --entrypoint /bin/sh jbergknoff/postgresql-client
```

`dbdump.sh`:
```
DATE=$( date +%Y%m%d)
echo $DATE
docker run -e PGPASSWORD=$DB_PASS  boris42/pg_dump pg_dump -h $DB_HOST -d $DB_NAME -U $DB_USER > db_backup/$DATE.sql
gzip db_backup/$DATE.sql
```

Install the following crontab:
```
0 16 * * * find ~/db_backup -type f -mtime +10 -exec rm \{\} \;
1 16 * * * . ~/dbenv.sh && ~/dbdump.sh
```

To save running costs, the instance can be stopped when not in use. This means the crontab won't run, so it would be necessary to start the instance when needed and run the dbdump script manually.

## Populate the QA database from the live one

Open a shell on the db instance.

We can't drop the QA database while the EB webserver is connected, so either:
* create a new empty db under a new name, then update the EB configuration for QA to use the new one
* OR scale the QA instance down to zero.

Then, open a postgres client by running `dbshell.sh` and delete the old QA db with `DROP DATABASE [OLD_QA_DB_NAME]`.

Now run `dbclient.sh` to open a shell in the postgres client docker container. Paste in contents of the appropriate `_env.sh` file to export db connection params.

Dump the prod db in tar format:

```
pg_dump -U $DB_USER -h $DB_HOST -F t [PROD_DB_NAME]> /tmp/cegovdb.tar
```

Now populate the new empty QA db with the dumped tarfile:

```
pg_restore -U $DB_USER -h $DB_HOST -d [NEW_QA_DB_NAME] cegovdb.tar
```


## Database permission setup

TODO: implement separate users so we are not just running on postgres user in all envs

The default postgres permissions setup allows all users to connect to all databases. When "trust authenticaion" is used (which is is in the docker container used locally), no password is required.

The AWS environments use RDS which is configured separately. Each environment (prod/qa) has its own database and must have a separate username and password to access it.

The `postgres` user is the superuser. A "role" is basically a user.

In `psql`, Use `\du` to see a list of roles, and `select CURRENT_USER` to see which user you are currently logged in as. The `\l` command to list databases also shows their access privileges.

As postgres user, when creating a new database, run

CREATE DATABASE cegov;
REVOKE CONNECT ON DATABASE cegov FROM public;

This prevents public access to the new db. Then create a specific user with

CREATE USER dev_user WITH PASSWORD 'woof';
GRANT ALL ON DATABASE cegov TO dev_user;

Then for existing databases, the ownership of all existing objects needs to change. Need more work on this bit.
