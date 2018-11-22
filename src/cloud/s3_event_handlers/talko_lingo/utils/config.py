import os

import boto3


def get_pipeline_config():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['PIPELINE_CONFIG_TABLE_NAME'])
    items = table.scan()['Items']

    return {item['ParameterName']: item['ParameterValue'] for item in items}


def get_device_languages():
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DEVICE_CONFIG_TABLE_NAME'])
    items = table.scan()['Items']
    device_a_config = next(filter(lambda item: item['DeviceId'] == 'device_a', items))
    device_b_config = next(filter(lambda item: item['DeviceId'] == 'device_b', items))

    return {
        'device_a': device_a_config['Lang'],
        'device_b': device_b_config['Lang'],
    }
