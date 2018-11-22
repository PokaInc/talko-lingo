import json
import os
import uuid

import boto3
from google.cloud import speech, texttospeech
from google.cloud.speech import enums, types

from talko_lingo.utils.config import get_device_languages, get_pipeline_config
from talko_lingo.utils.job_id import build_job_id, extract_output_device_from_job_id, \
    extract_input_output_lang_from_job_id
from talko_lingo.utils.translate import translate


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
    input_device_id = key.rpartition('/')[0].rpartition('/')[2]
    output_device_id = 'device_b' if input_device_id == 'device_a' else 'device_a'

    device_languages = get_device_languages()
    input_lang = device_languages[input_device_id]
    output_lang = device_languages[output_device_id]

    job_id = build_job_id(input_device_id, input_lang, output_device_id, output_lang)

    publish_status('Transcribing', job_id=job_id)

    pipeline_config = get_pipeline_config()
    transcribe_mode = pipeline_config.get('TranscribeMode', 'aws')

    if transcribe_mode == 'aws':
        if input_lang == 'en-US':
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
            print(text_to_translate)
            publish_status('Translating', job_id=job_id, TextToTranslate=text_to_translate)
            translated_text = translate(text_to_translate, bucketname, job_id=job_id)
            text_to_speech(translated_text, bucketname, job_id=job_id)
        else:
            transcribe_client = boto3.client('transcribe')
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

    else:
        client = speech.SpeechClient()

        content = boto3.client('s3').get_object(Bucket=bucketname, Key=key)['Body'].read()
        audio = types.RecognitionAudio(content=content)

        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,
            language_code=input_lang
        )

        response = client.recognize(config, audio)

        print(response)
        if response.results:
            text_to_translate = response.results[0].alternatives[0].transcript
            publish_status('Translating', job_id=job_id, TextToTranslate=text_to_translate)
            translated_text = translate(text_to_translate, job_id)
            text_to_speech(translated_text, bucketname, job_id=job_id)
        else:
            publish_status('Error', job_id=job_id, ErrorCause='speech-to-text')


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
        topic='talko/rx/' + extract_output_device_from_job_id(job_id),
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

    publish_status('Translating', job_id=job_id, TextToTranslate=text_to_translate)
    translated_text = translate(text_to_translate, job_id=job_id)
    text_to_speech(translated_text, bucketname, job_id=job_id)


def text_to_speech(text, bucketname, job_id):
    pipeline_config = get_pipeline_config()

    publish_status('Pollying', job_id=job_id, TextToPolly=text)

    _, output_lang = extract_input_output_lang_from_job_id(job_id)

    text_to_speech_mode = pipeline_config.get('TextToSpeechMode', 'aws')
    if text_to_speech_mode == 'aws':
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
    else:
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.types.SynthesisInput(text=text)

        voice = texttospeech.types.VoiceSelectionParams(
            language_code=output_lang,
            ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE,
        )

        audio_config = texttospeech.types.AudioConfig(
            audio_encoding=texttospeech.enums.AudioEncoding.MP3,
        )

        response = client.synthesize_speech(synthesis_input, voice, audio_config)

        s3 = boto3.resource('s3')
        key = 'output/{}/{}.mp3'.format(job_id, str(uuid.uuid4()))
        s3object = s3.Object(bucketname, key)
        s3object.put(Body=response.audio_content)


def publish_status(status, job_id, **data):
    iot = boto3.client('iot-data')
    iot.publish(topic='talko/job_status', payload=json.dumps({
        'JobId': job_id,
        'Status': status,
        'Data': data or None,
    }))
