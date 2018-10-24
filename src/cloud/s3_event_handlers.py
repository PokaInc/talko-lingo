import json
import os
import uuid

import boto3


def lambda_handler(event, _):
    s3_client = boto3.client('s3')
    records = event['Records']
    for record in records:
        message = json.loads(record['Sns']['Message'])
        message_records = message.get('Records', [])
        for message_record in message_records:
            s3_message = message_record['s3']
            bucketname = s3_message['bucket']['name']
            key = s3_message['object']['key']

            if key.startswith('input/'):
                handle_new_audio_file(bucketname, key)
            if key.startswith('output/'):
                handle_polly_generated_file(s3_client, bucketname, key)
            elif '/' not in key and key.endswith('.json'):
                handle_new_transcription_result(s3_client, bucketname, key)


def handle_new_audio_file(bucketname, key):
    transcribe_client = boto3.client('transcribe')
    publish_message('Transcribing')
    response = transcribe_client.start_transcription_job(
        TranscriptionJobName=str(uuid.uuid4()),
        LanguageCode='en-US',
        MediaFormat=os.path.splitext(key)[1][1:],
        Media={
            'MediaFileUri': f'https://s3.amazonaws.com/{bucketname}/{key}'
        },
        OutputBucketName=bucketname
    )
    print(response)


def build_presigned_url(s3_client, bucketname, key):
    return s3_client.generate_presigned_url(
        ClientMethod='get_object',
        ExpiresIn=900,
        Params={
            'Bucket': bucketname,
            'Key': key,
        }
    )


def handle_polly_generated_file(s3_client, bucketname, key):
    publish_message('Publishing')
    iot_client = boto3.client('iot-data')
    print(iot_client.publish(
        topic='talko/rx',
        payload=json.dumps({
            'AudioFileUrl': build_presigned_url(s3_client, bucketname, key)
        }).encode('utf-8')
    ))


def handle_new_transcription_result(s3_client, bucketname, key):
    publish_message('Translating')
    content = json.loads(s3_client.get_object(Bucket=bucketname, Key=key)['Body'].read())
    translate_client = boto3.client('translate')
    translated_text = translate_client.translate_text(
        Text=content['results']['transcripts'][0]['transcript'],
        SourceLanguageCode='en',
        TargetLanguageCode='fr'
    )['TranslatedText']
    print('Translated text: ' + translated_text)
    create_polly_job(translated_text, bucketname)


def create_polly_job(text, bucketname):
    publish_message('Pollying')
    polly_client = boto3.client('polly')
    print(polly_client.start_speech_synthesis_task(
        OutputFormat='mp3',
        OutputS3BucketName=bucketname,
        OutputS3KeyPrefix='output/',
        Text=text,
        VoiceId='Chantal',
        LanguageCode='fr-CA'
    ))


def publish_message(msg):
    sns = boto3.resource('sns')
    topic = sns.Topic(os.environ['STATUS_TOPIC_ARN'])
    print(topic.publish(
        Message=msg,
    ))
