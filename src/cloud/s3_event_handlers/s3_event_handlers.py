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
                    handle_polly_generated_file(s3_client, bucketname, key)


def handle_new_audio_file(bucketname, key):
    # dynamodb = boto3.resource('dynamodb')
    # table = dynamodb.Table(os.environ['JOBS_TABLE_NAME'])

    input_language = 'en-US'  # todo: dynamically get input language

    if input_language == 'en-US':
        lambda_client = boto3.client('lambda')
        response = lambda_client.invoke(
            FunctionName=os.environ['ENGLISH_TRANSCRIBE_STREAMING_LAMBDA_FUNCTION_NAME'],
            InvocationType='RequestResponse',
            Payload=json.dumps({
                "bucketName": bucketname,
                "objectKey": key,
            }),
        )

        text_to_translate = response['Payload'].read().decode('utf-8')
        translate(text_to_translate, bucketname)
    else:
        transcribe_client = boto3.client('transcribe')
        publish_message('Transcribing')
        response = transcribe_client.start_transcription_job(
            TranscriptionJobName=str(uuid.uuid4()),
            LanguageCode=input_language,
            MediaFormat=os.path.splitext(key)[1][1:],
            Media={
                'MediaFileUri': f'https://s3.amazonaws.com/{bucketname}/{key}'
            },
            OutputBucketName=bucketname
        )
        print(response)
    # table.put_item(
    #     Item={
    #         'InputKey': key,
    #         'TranscribeResponse': json.dumps(response),
    #     }
    # )


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


def handle_transcribe_event(event):
    detail = event['detail']
    if detail['TranscriptionJobStatus'] != 'COMPLETED':
        return

    publish_message('Translating')
    transcription_job_name = detail['TranscriptionJobName']
    transcribe = boto3.client('transcribe')
    response = transcribe.get_transcription_job(
        TranscriptionJobName=transcription_job_name
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
    translate(text_to_translate, bucketname)


def translate(text_to_translate, destination_bucket_namt):
    translate_client = boto3.client('translate')
    translated_text = translate_client.translate_text(
        Text=text_to_translate,
        SourceLanguageCode='en',
        TargetLanguageCode='fr'
    )['TranslatedText']
    print('Translated text: ' + translated_text)
    create_polly_job(translated_text, destination_bucket_namt)


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
    # sns = boto3.resource('sns')
    # topic = sns.Topic(os.environ['STATUS_TOPIC_ARN'])
    # print(topic.publish(
    #     Message=msg,
    # ))
    iot = boto3.client('iot-data')
    iot.publish(topic='bleh', payload=msg)
