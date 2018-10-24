#!/bin/bash

set -e

# Create a temporary directory
TEMP_DIR=`mktemp -d`

# Add the actual code
pushd src/local
rsync -a --include '*/' --include '*.py' --exclude '*' . ${TEMP_DIR}
popd
# Copy the Greengrass SDK
pushd vendored
rsync -a --include '*/' --include '*.py' --exclude '*' . ${TEMP_DIR}
popd

# Finally let's bundle this
pushd ${TEMP_DIR}
zip -r local_lambdas.zip ./*
popd

# Copy the tmp file back to the dist directory so it can be uploaded
cp ${TEMP_DIR}/local_lambdas.zip dist/
