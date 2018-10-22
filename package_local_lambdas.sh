#!/bin/bash

set -e

# Create a temporary directory
TEMP_DIR=`mktemp -d`

# Add the actual code
pushd src
rsync -a --include '*/' --include '*.py' --exclude '*' . ${TEMP_DIR}
popd
# Copy the Greengrass SDK
pushd vendored
rsync -a --include '*/' --include '*.py' --exclude '*' . ${TEMP_DIR}
popd

# Finally let's bundle this
pushd ${TEMP_DIR}
zip -r talko_lingo_greengrass_lambdas.zip ./*
popd

# Copy the tmp file back to the dist directory so it can be uploaded
cp ${TEMP_DIR}/talko_lingo_greengrass_lambdas.zip dist/
