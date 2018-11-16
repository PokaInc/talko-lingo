import os

import boto3


def lambda_handler(event, context):
    device_id = event['device_id']
    lang = event['lang']

    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DEVICE_CONFIG_TABLE_NAME'])

    table.put_item(
        Item={
            'DeviceId': device_id,
            'Lang': lang,
        }
    )
