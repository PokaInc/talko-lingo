import os

import boto3

from audio_recorder import AudioRecorder
from physical_inputs import PhysicalInterface

RECORDING_DEVICE_NAME = os.environ['RECORDING_DEVICE_NAME']
BUCKET_NAME = os.environ['TALKO_LINGO_BUCKET']
shift_key_pressed = False

s3_resource = boto3.resource('s3')
bucket = s3_resource.Bucket(BUCKET_NAME)


def on_new_recording(recording):
    bucket.upload_file(recording.filename, 'input/' + os.path.basename(recording.filename))


with PhysicalInterface as physical_interface:
    with AudioRecorder(RECORDING_DEVICE_NAME, on_new_recording) as audio_recorder:
        try:
            while True:
                audio_recorder.tick(physical_interface.is_push_to_talk_button_pressed())
        except KeyboardInterrupt:
            pass


def dummy_handler(event, context):
    pass
