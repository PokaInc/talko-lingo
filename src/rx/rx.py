import subprocess


def rx_handler(event, context):
    # mpg321 doesn't recognize URLs unless they start with http://
    audio_file_url = event['AUDIO_FILE_URL'].replace('https://', 'http://')
    subprocess.call(['mpg321', audio_file_url])
