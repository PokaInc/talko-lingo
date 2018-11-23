import json
import os

import boto3
from google.cloud import speech
from google.cloud.speech import enums, types
from talko_lingo.utils.config import get_pipeline_config


class AwsSpeechToText(object):
    def run(self, input_s3object, input_lang, job_id):
        if input_lang == 'en-US':
            lambda_client = boto3.client('lambda')

            response = lambda_client.invoke(
                FunctionName=os.environ['ENGLISH_TRANSCRIBE_STREAMING_LAMBDA_FUNCTION_NAME'],
                InvocationType='RequestResponse',
                Payload=json.dumps({
                    "bucketName": input_s3object.bucket_name,
                    "objectKey": input_s3object.key,
                }),
            )

            text = response['Payload'].read().decode('utf-8')
            print('Text:', text)
            return text, False
        else:
            transcribe_client = boto3.client('transcribe')
            transcribe_client.start_transcription_job(
                TranscriptionJobName=job_id,
                LanguageCode=input_lang,
                MediaFormat=os.path.splitext(input_s3object.key)[1][1:],
                Media={
                    'MediaFileUri': 'https://s3.amazonaws.com/{}/{}'.format(bucketname, key)
                },
                OutputBucketName=input_s3object.bucket_name
            )
            return None, True


class GcpSpeechToText(object):
    def run(self, input_s3object, input_lang, job_id):
        client = speech.SpeechClient()

        content = input_s3object.get()['Body'].read()
        audio = types.RecognitionAudio(content=content)

        config = types.RecognitionConfig(
            encoding=enums.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=44100,
            language_code=input_lang
        )

        response = client.recognize(config, audio)

        print(response)
        if response.results:
            text = response.results[0].alternatives[0].transcript
            return text, False
        else:
            return None, False


def speech_to_text(input_s3object, input_lang, job_id):
    pipeline_config = get_pipeline_config()
    speech_to_text_mode = pipeline_config.get('SpeechToTextMode', 'aws')
    speech_to_text_class = AwsSpeechToText if speech_to_text_mode == 'aws' else GcpSpeechToText
    text, async = speech_to_text_class().run(input_s3object=input_s3object, input_lang=input_lang, job_id=job_id)
    return text, async
