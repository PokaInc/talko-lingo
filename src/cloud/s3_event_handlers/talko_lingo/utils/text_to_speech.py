import uuid

import boto3
from google.cloud import texttospeech
from talko_lingo.utils.config import get_pipeline_config
from talko_lingo.utils.job_id import extract_input_output_lang_from_job_id


class AwsTextToSpeech(object):
    def run(self, text, output_bucket, job_id):
        _, output_lang = extract_input_output_lang_from_job_id(job_id)
        voices = {
            'fr-CA': 'Chantal',
            'en-AU': 'Nicole',
            'en-US': 'Joanna',
            'en-GB': 'Emma',
            'es-US': 'Penelope',
        }

        polly_client = boto3.client('polly')
        polly_client.start_speech_synthesis_task(
            OutputFormat='mp3',
            OutputS3BucketName=output_bucket.name,
            OutputS3KeyPrefix='output/{}/'.format(job_id),
            Text=text,
            VoiceId=voices[output_lang],
            LanguageCode=output_lang
        )


class GcpTextToSpeech(object):
    def run(self, text, output_bucket, job_id):
        _, output_lang = extract_input_output_lang_from_job_id(job_id)
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
        s3object = s3.Object(output_bucket.name, key)
        s3object.put(Body=response.audio_content)


def text_to_speech(text, output_bucket, job_id):
    pipeline_config = get_pipeline_config()
    text_to_speech_mode = pipeline_config.get('TextToSpeechMode', 'aws')
    text_to_speech_class = AwsTextToSpeech if text_to_speech_mode == 'aws' else GcpTextToSpeech
    text_to_speech_class().run(text=text, output_bucket=output_bucket, job_id=job_id)
