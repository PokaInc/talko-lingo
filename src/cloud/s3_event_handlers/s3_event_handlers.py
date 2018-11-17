import json
import os
import uuid

import boto3


def lambda_handler(event, _):
    print('event:', event)
    if event.get('source') == 'aws.transcribe':
        handle_transcribe_event(event)
    else:
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
                    job_id = key.partition('output/')[2].partition('/')[0]
                    handle_polly_generated_file(s3_client, bucketname, key, job_id=job_id)


def handle_new_audio_file(bucketname, key):
    job_id = str(uuid.uuid4())

    input_language = 'en-US'  # todo: dynamically get input language

    if input_language == 'en-US':
        lambda_client = boto3.client('lambda')
        publish_status('Transcribing', job_id=job_id)
        response = lambda_client.invoke(
            FunctionName=os.environ['ENGLISH_TRANSCRIBE_STREAMING_LAMBDA_FUNCTION_NAME'],
            InvocationType='RequestResponse',
            Payload=json.dumps({
                "bucketName": bucketname,
                "objectKey": key,
            }),
        )

        text_to_translate = response['Payload'].read().decode('utf-8')
        print(text_to_translate)
        translate(text_to_translate, bucketname, job_id=job_id)
    else:
        transcribe_client = boto3.client('transcribe')
        publish_status('Transcribing', job_id=job_id)
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=job_id,
            LanguageCode=input_language,
            MediaFormat=os.path.splitext(key)[1][1:],
            Media={
                'MediaFileUri': 'https://s3.amazonaws.com/{}/{}'.format(bucketname, key)
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


def handle_polly_generated_file(s3_client, bucketname, key, job_id):
    publish_status('Publishing', job_id=job_id)
    iot_client = boto3.client('iot-data')
    print(iot_client.publish(
        topic='talko/rx',
        payload=json.dumps({
            'AudioFileUrl': build_presigned_url(s3_client, bucketname, key)
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
    bucket_and_key = transcript_file_uri.partition('https://s3.amazonaws.com')[2]
    print(bucket_and_key)
    bucketname, _, key = bucket_and_key.partition('/')
    print(bucketname)
    print(_)
    print(key)

    content = json.loads(boto3.client('s3').get_object(Bucket=bucketname, Key=key)['Body'].read())
    text_to_translate = content['results']['transcripts'][0]['transcript']
    translate(text_to_translate, bucketname, job_id=job_id)


def translate(text_to_translate, destination_bucket_name, job_id):
    publish_status('Translating', job_id=job_id)
    translate_client = boto3.client('translate')
    translated_text = translate_client.translate_text(
        Text=text_to_translate,
        SourceLanguageCode='en',
        TargetLanguageCode='fr'
    )['TranslatedText']
    print('Translated text: ' + translated_text)
    create_polly_job(translated_text, destination_bucket_name, job_id=job_id)


def create_polly_job(text, bucketname, job_id):
    publish_status('Pollying', job_id=job_id)
    polly_client = boto3.client('polly')
    print(polly_client.start_speech_synthesis_task(
        OutputFormat='mp3',
        OutputS3BucketName=bucketname,
        OutputS3KeyPrefix='output/{}/'.format(job_id),
        Text=text,
        VoiceId='Chantal',
        LanguageCode='fr-CA'
    ))


def publish_status(status, job_id):
    iot = boto3.client('iot-data')
    iot.publish(topic='job_status', payload=json.dumps({
        'JobId': job_id,
        'Status': status,
    }))
