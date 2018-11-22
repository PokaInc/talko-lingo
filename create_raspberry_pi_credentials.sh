#!/usr/bin/env bash

set -e

TEMPLATE_FILE=$1
STACK_NAME=$2
TALKO_LINGO_STACK_NAME=$3


function SetupDeviceCredentials {
    DEVICE_STACK_NAME=${STACK_NAME}-$1
    
    TMP_FOLDER=$(mktemp -d /tmp/XXXXXX)

    PRIVATE_KEY=${TMP_FOLDER}/iot-device-$1.key
    CSR=${TMP_FOLDER}/iot-device-$1.csr
    openssl genrsa -out ${PRIVATE_KEY} 2048
    openssl req -new -sha256 -subj "/C=US/ST=./L=./O=./CN=." -key ${PRIVATE_KEY} -out ${CSR}

    aws cloudformation deploy --template-file ${TEMPLATE_FILE} --stack-name ${DEVICE_STACK_NAME} --parameter-overrides Csr="$(cat ${CSR})" --capabilities CAPABILITY_IAM
    CONFIGURATION_BUCKET=$(aws cloudformation describe-stacks --stack-name ${DEVICE_STACK_NAME} --query "Stacks[0].Outputs[?OutputKey=='ConfigurationBucket'].OutputValue" --output text)

    ACCESS_KEY_ID=$(aws cloudformation describe-stacks --stack-name ${DEVICE_STACK_NAME} --query "Stacks[0].Outputs[?OutputKey=='AccessKeyId'].OutputValue" --output text)
    SECRET_ACCESS_KEY_SECRET_ARN=$(aws cloudformation describe-stacks --stack-name ${DEVICE_STACK_NAME} --query "Stacks[0].Outputs[?OutputKey=='SecretAccessKeySecretArn'].OutputValue" --output text)
    SECRET_ACCESS_KEY=$(aws secretsmanager get-secret-value --secret-id ${SECRET_ACCESS_KEY_SECRET_ARN} --query "SecretString" --output text)

    IOT_CERTIFICATE_ID=$(aws cloudformation describe-stacks --stack-name ${DEVICE_STACK_NAME} --query "Stacks[0].Outputs[?OutputKey=='IotCertificateId'].OutputValue" --output text)

    AUDIO_FILE_STORE=$(aws cloudformation describe-stacks --stack-name ${TALKO_LINGO_STACK_NAME} --query "Stacks[0].Outputs[?OutputKey=='AudioFileStore'].OutputValue" --output text)

    CRT=${TMP_FOLDER}/iot-device-$1.crt
    aws iot describe-certificate --certificate-id ${IOT_CERTIFICATE_ID} --query 'certificateDescription.certificatePem' --output text > ${CRT}

    AMAZON_ROOT_CA=${TMP_FOLDER}/AmazonRootCA1.pem
    wget https://www.amazontrust.com/repository/AmazonRootCA1.pem -O ${AMAZON_ROOT_CA}

    CONFIGURATION=${TMP_FOLDER}/environment

    echo "--------------------------------------------------------"
    echo "Execute the following on device $1 terminal: "

    cat << EOF > ${CONFIGURATION}
DEVICE_ID=device_$(echo $1 | awk '{print tolower($0)}')
AWS_ACCESS_KEY_ID=${ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${SECRET_ACCESS_KEY}
AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-`aws configure get region`}
IOT_ENDPOINT=$(aws iot describe-endpoint --endpoint-type iot:Data-ATS --query endpointAddress --output text)
IOT_ENDPOINT_PORT=8883
AUDIO_FILE_STORE=${AUDIO_FILE_STORE}
AMAZON_ROOT_CA=AmazonRootCA1.pem
PRIVATE_KEY=iot-device-$1.key
CRT=iot-device-$1.crt
EOF

    pushd ${TMP_FOLDER}
    zip config.zip *
    popd

    KEY=s3://${CONFIGURATION_BUCKET}/config.zip
    aws s3 cp ${TMP_FOLDER}/config.zip ${KEY} > /dev/null
    URL=$(aws s3 presign --expires-in 900 ${KEY})
    echo "wget \"${URL}\" -O config.zip && unzip config.zip -d /home/pi/talko-lingo/.config && rm config.zip"

    echo "-----------(Link will expire in 15 minutes)-------------"

    rm ${TMP_FOLDER}/*
}

echo "Generating credentials for device A..."
SetupDeviceCredentials A

read -p "Press enter to continue"

echo "Generating credentials for device B..."
SetupDeviceCredentials B
