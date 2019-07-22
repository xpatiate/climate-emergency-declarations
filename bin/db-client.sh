PSQL=$(which psql)
if [ -z "$PSQL" ]
then
    apt-get update
    apt-get install postgresql-client
    PSQL=$(which psql)
fi
echo $DB_PASS
$PSQL -h $DB_HOST -U $DB_USER $DB_NAME
