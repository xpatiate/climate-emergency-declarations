#!/bin/bash

set -ex

AWS_PROFILE=xpatiate
LAMBDA_NAME=cegov_qa_handler
LAMBDA_FILE=django-function-3.7.zip
S3_BUCKET=cegov-lambda-function-code

ZIP_PATH=/tmp/$LAMBDA_FILE
AWS_PSYCO_PATH=~/repo/awslambda-psycopg2/psycopg2-3.7
REPO_DIR=~/cegov

if [[ -f $ZIP_PATH ]]
then
    rm $ZIP_PATH
fi

PKGS="Django==3.0.2 boto3"

# install virtualenv pkgs
VENVDIR=/tmp/django-venv-$$
mkdir $VENVDIR
cd $VENVDIR
python3 -m venv .venv
. .venv/bin/activate
pip3 install $PKGS
deactivate
#cd .venv/lib/python*/site-packages/
mv .venv/lib/python3.6/site-packages lib

# copy in psycopg2 pkg
cp -R $AWS_PSYCO_PATH lib/psycopg2

# create zipfile with dependencies in lib
zip -r $ZIP_PATH lib

# Now add the custom components
cd $REPO_DIR
zip -r $ZIP_PATH api ced_bg govtrack run_background_task.py

echo "Made zip file at $ZIP_PATH"

exit 0

# upload to S3
echo aws s3 something

# update lambda to pull new code from S3
echo aws --profile=$AWS_PROFILE lambda update-function-code --function-name $LAMBDA_NAME --s3-bucket $S3_BUCKET --s3-key $LAMBDA_FILE
