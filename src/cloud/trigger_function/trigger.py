import json
import os

import boto3


def handler(event, context):
    lambda_client = boto3.client('lambda')
    response = lambda_client.invoke(
        FunctionName=os.environ['EnglishTranscribeStreamingLambdaFunctionArn'],
        InvocationType='RequestResponse',
        Payload=json.dumps({
            "bucketName": "talkolingo-audiofilestore-10log5mrxrr34",
            "objectKey": "input/SP-MacBook-Pro.local/en/out.wav"
        }),
    )

    print(response['Payload'].read())
