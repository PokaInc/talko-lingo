import json

import boto3

from talko_lingo.utils.speech_to_text import speech_to_text
from talko_lingo.utils.config import get_device_languages
from talko_lingo.utils.job_id import build_job_id, extract_output_device_from_job_id
from talko_lingo.utils.messaging import publish_status
from talko_lingo.utils.text_to_speech import text_to_speech
from talko_lingo.utils.translate import translate


def lambda_handler(event, _):
    print('event:', event)
    if event.get('source') == 'aws.transcribe':
        handle_transcribe_event(event)
    else:
        records = event['Records']
        for record in records:
            message = json.loads(record['Sns']['Message'])
            message_records = message.get('Records', [])
            for message_record in message_records:
                s3_message = message_record['s3']
                s3object = boto3.resource('s3').Object(s3_message['bucket']['name'], s3_message['object']['key'])

                if s3object.key.startswith('input/'):
                    handle_input_file(s3object)
                if s3object.key.startswith('output/'):
                    handle_output_file(s3object)


def handle_input_file(s3object):
    input_device_id = s3object.key.rpartition('/')[0].rpartition('/')[2]
    output_device_id = 'device_b' if input_device_id == 'device_a' else 'device_a'

    device_languages = get_device_languages()
    input_lang = device_languages[input_device_id]
    output_lang = device_languages[output_device_id]

    cloudwatch = boto3.client('cloudwatch')
    cloudwatch.put_metric_data(
        Namespace='talko-lingo/s3eventhandlers',
        MetricData=[
            {
                'MetricName': 'InputFilesProcessed',
                'Value': 1,
                'Dimensions': [
                    {
                        'Name': 'InputLang',
                        'Value': input_lang,
                    },
                    {
                        'Name': 'OutputLang',
                        'Value': output_lang,
                    },
                ],
                'Unit': 'Count',
            },
        ]
    )

    job_id = build_job_id(input_device_id, input_lang, output_device_id, output_lang)

    publish_status('SpeechToText', job_id=job_id)
    text_to_translate, async = speech_to_text(s3object, input_lang, job_id)

    if text_to_translate is not None and async is False:
        on_speech_to_text_done(text_to_translate, output_bucket=boto3.resource('s3').Bucket(s3object.bucket_name),
                               job_id=job_id)
    elif text_to_translate is None and async is False:
        publish_status('Error', job_id=job_id, ErrorCause='speech-to-text')


def on_speech_to_text_done(text_to_translate, output_bucket, job_id):
    publish_status('Translating', job_id=job_id, Text=text_to_translate)
    translated_text = translate(text_to_translate, job_id=job_id)

    publish_status('TextToSpeech', job_id=job_id, Text=translated_text)
    text_to_speech(translated_text, output_bucket=output_bucket, job_id=job_id)


def handle_output_file(s3object):
    job_id = s3object.key.partition('output/')[2].partition('/')[0]
    publish_status('Publishing', job_id=job_id)
    iot_client = boto3.client('iot-data')
    presigned_url = boto3.client('s3').generate_presigned_url(
        ClientMethod='get_object',
        ExpiresIn=900,
        Params={
            'Bucket': s3object.bucket_name,
            'Key': s3object.key,
        }
    )
    print(iot_client.publish(
        topic='talko/rx/' + extract_output_device_from_job_id(job_id),
        payload=json.dumps({
            'AudioFileUrl': presigned_url
        }).encode('utf-8')
    ))


def handle_transcribe_event(event):
    detail = event['detail']
    if detail['TranscriptionJobStatus'] != 'COMPLETED':
        return

    job_id = detail['TranscriptionJobName']
    transcribe = boto3.client('transcribe')
    response = transcribe.get_transcription_job(
        TranscriptionJobName=job_id
    )
    print('transcription job:', response)
    transcript_file_uri = response['TranscriptionJob']['Transcript']['TranscriptFileUri']
    bucket_and_key = transcript_file_uri.partition('https://s3.amazonaws.com/')[2]
    bucketname, _, key = bucket_and_key.partition('/')

    content = json.loads(boto3.client('s3').get_object(Bucket=bucketname, Key=key)['Body'].read())
    text_to_translate = content['results']['transcripts'][0]['transcript']
    on_speech_to_text_done(text_to_translate=text_to_translate, output_bucket=boto3.resource('s3').Bucket(bucketname),
                           job_id=job_id)
