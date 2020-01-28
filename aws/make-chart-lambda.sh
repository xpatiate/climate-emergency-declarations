#!/bin/bash

set -ex

AWS_PROFILE=xpatiate
LAMBDA_NAME=qa_chart
LAMBDA_FILE=chart-function.zip
S3_BUCKET=cegov-lambda-function-code

ZIP_PATH=/tmp/$LAMBDA_FILE
REPO_DIR=~/cegov

if [[ -f $ZIP_PATH ]]
then
    rm $ZIP_PATH
fi

PKGS="pandas matplotlib requests"

# install virtualenv pkgs
VENVDIR=/tmp/django-venv-$$
mkdir $VENVDIR
cd $VENVDIR
python3 -m venv .venv
. .venv/bin/activate
pip3 install $PKGS
deactivate
mv .venv/lib/python3.6/site-packages lib

# create zipfile with dependencies in lib
zip -r $ZIP_PATH lib

# Now add the custom components
cd $REPO_DIR/lambda
zip -r $ZIP_PATH generate_chart.py

echo "Made zip file at $ZIP_PATH"

exit 0

# upload to S3
echo aws s3 something

# update lambda to pull new code from S3
echo aws --profile=$AWS_PROFILE lambda update-function-code --function-name $LAMBDA_NAME --s3-bucket $S3_BUCKET --s3-key $LAMBDA_FILE


# ok try this
# https://medium.com/i-like-big-data-and-i-cannot-lie/how-to-create-an-aws-lambda-python-3-6-deployment-package-using-docker-d0e847207dd6
# locally run:
# docker run -it dacut/amazon-linux-python-3.6
# inside container, create dir, install any deps into the dir:
# pip3 install <PACKAGE_NAME> -t ./
# zip the dir and copy zip file from container
# add lambda function script to zip
# then upload
