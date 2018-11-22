# Note: This code has mostly been taken from https://github.com/mariocannistra/python-paho-mqtt-for-aws-iot

import paho.mqtt.client as paho
import os
import socket
import ssl
import json
import subprocess


def on_connect(client, userdata, flags, rc):
    print("Connection returned result: " + str(rc))
    client.subscribe("talko/rx/" + os.environ['DEVICE_ID'], 1)


def on_message(client, userdata, msg):
    print("topic: "+msg.topic)
    print("payload: "+str(msg.payload))
    payload = json.loads(msg.payload)
    audio_file_url = payload["AudioFileUrl"]
    print("Playing: {}".format(audio_file_url))
    subprocess.call(['mpg321', audio_file_url.replace("https://", "http://")])


mqttc = paho.Client()
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.tls_set(
    os.environ['AMAZON_ROOT_CA'],
    certfile=os.environ['CRT'],
    keyfile=os.environ['PRIVATE_KEY'],
    cert_reqs=ssl.CERT_REQUIRED,
    tls_version=ssl.PROTOCOL_TLSv1_2,
    ciphers=None
)
mqttc.connect(os.environ['IOT_ENDPOINT'], os.environ['IOT_ENDPOINT_PORT'], keepalive=60)
mqttc.loop_forever()


def dummy_handler(event, context):
    pass
