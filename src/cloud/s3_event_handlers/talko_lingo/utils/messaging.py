import json

import boto3


def publish_status(status, job_id, **data):
    iot = boto3.client('iot-data')
    iot.publish(topic='talko/job_status', payload=json.dumps({
        'JobId': job_id,
        'Status': status,
        'Data': data or None,
    }))
