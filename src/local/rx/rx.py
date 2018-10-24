import subprocess


def handler(event, _):
    # mpg321 doesn't recognize URLs unless they start with http://
    audio_file_url = event['AudioFileUrl'].replace('https://', 'http://')
    subprocess.call(['mpg321', audio_file_url])
