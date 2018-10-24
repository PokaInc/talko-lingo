import os
import socket
from time import sleep

import boto3

from audio_recorder import AudioRecorder
from physical_inputs import PhysicalInterface
from shared.display import Display

RECORDING_DEVICE_NAME = os.environ['RECORDING_DEVICE_NAME']
BUCKET_NAME = os.environ['AUDIO_FILE_STORE']
current_language_code = 'en'

s3_resource = boto3.resource('s3')
bucket = s3_resource.Bucket(BUCKET_NAME)

display = Display()
print('=== {} READY ==='.format(display.__class__.__name__))


def on_new_recording(recording):
    local_path = recording.filename
    s3_path = 'input/{hostname}/{language_code}/{filename}'.format(
        hostname=socket.gethostname(),
        language_code=current_language_code,
        filename=os.path.basename(recording.filename),
    )
    bucket.upload_file(local_path, s3_path)
    print('File successfully uploaded: ' + s3_path)


def on_language_change(language_code):
    global current_language_code
    current_language_code = language_code
    display.show(' {} '.format(language_code))


with PhysicalInterface as physical_interface:
    physical_interface.on_language_change = on_language_change
    print('=== {} READY ==='.format(physical_interface.__class__.__name__))
    with AudioRecorder(RECORDING_DEVICE_NAME) as audio_recorder:
        audio_recorder.completion_callback = on_new_recording
        print('=== {} READY ==='.format(audio_recorder.__class__.__name__))
        try:
            while True:
                physical_interface.tick()
                audio_recorder.tick(physical_interface.is_push_to_talk_button_pressed)
                sleep(0.05)
        except KeyboardInterrupt:
            pass


def dummy_handler(event, context):
    pass
