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


def handle_new_audio_file(bucketname, key):
    device_id = key.rpartition('/')[0].rpartition('/')[2]
    device_languages = get_device_languages()
    if device_id == 'device_a':
        input_lang = device_languages['device_a']
        output_lang = device_languages['device_b']
    else:
        input_lang = device_languages['device_b']
        output_lang = device_languages['device_a']

    job_id = build_job_id(input_lang, output_lang)

    if input_lang == 'en-US':
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
            LanguageCode=input_lang,
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
    bucket_and_key = transcript_file_uri.partition('https://s3.amazonaws.com/')[2]
    bucketname, _, key = bucket_and_key.partition('/')

    content = json.loads(boto3.client('s3').get_object(Bucket=bucketname, Key=key)['Body'].read())
    text_to_translate = content['results']['transcripts'][0]['transcript']
    translate(text_to_translate, bucketname, job_id=job_id)


def translate(text_to_translate, destination_bucket_name, job_id):
    publish_status('Translating', job_id=job_id)

    input_lang, output_lang = extract_input_output_lang_from_job_id(job_id)

    # we're only interested in the first part of the code, e.g. en-US becomes en, fr-CA becomes fr
    input_lang = input_lang.split('-')[0]
    output_lang = output_lang.split('-')[0]

    translate_client = boto3.client('translate')
    translated_text = translate_client.translate_text(
        Text=text_to_translate,
        SourceLanguageCode=input_lang,
        TargetLanguageCode=output_lang
    )['TranslatedText']
    print('Translated text: ' + translated_text)
    create_polly_job(translated_text, destination_bucket_name, job_id=job_id)


def create_polly_job(text, bucketname, job_id):
    publish_status('Pollying', job_id=job_id)

    _, output_lang = extract_input_output_lang_from_job_id(job_id)

    voices = {
        'fr-CA': 'Chantal',
        'en-AU': 'Nicole',
        'en-US': 'Joanna',
        'en-GB': 'Emma',
        'es-US': 'Penelope',
    }

    polly_client = boto3.client('polly')
    print(polly_client.start_speech_synthesis_task(
        OutputFormat='mp3',
        OutputS3BucketName=bucketname,
        OutputS3KeyPrefix='output/{}/'.format(job_id),
        Text=text,
        VoiceId=voices[output_lang],
        LanguageCode=output_lang
    ))


def publish_status(status, job_id):
    iot = boto3.client('iot-data')
    iot.publish(topic='talko/job_status', payload=json.dumps({
        'JobId': job_id,
        'Status': status,
    }))


def build_job_id(input_lang, output_lang):
    return '{unique_id}_{input_lang}_{ouput_lang}'.format(
        unique_id=str(uuid.uuid4()),
        input_lang=input_lang,
        ouput_lang=output_lang,
    )


def extract_input_output_lang_from_job_id(job_id):
    parts = job_id.split('_')
    input_lang = parts[1]
    output_lang = parts[2]

    return input_lang, output_lang
