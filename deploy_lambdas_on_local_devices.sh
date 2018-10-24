#!/usr/bin/env bash

aws lambda publish-version --function-name
aws greengrass create-function-definition
