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
