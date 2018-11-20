# Note: This code has mostly been taken from https://github.com/mariocannistra/python-paho-mqtt-for-aws-iot

import paho.mqtt.client as paho
import os
import socket
import ssl
import json
import subprocess


def on_connect(client, userdata, flags, rc):
    print("Connection returned result: " + str(rc) )
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

awshost = "a2pbsc87z9l319-ats.iot.us-east-1.amazonaws.com"
awsport = 8883
clientId = "talko-lingo_Core"
thingName = "talko-lingo_Core"
caPath = "AmazonRootCA1.pem"
certPath = "2402aed9e0-certificate.pem.crt"
keyPath = "2402aed9e0-private.pem.key"

mqttc.tls_set(caPath, certfile=certPath, keyfile=keyPath, cert_reqs=ssl.CERT_REQUIRED, tls_version=ssl.PROTOCOL_TLSv1_2, ciphers=None)
mqttc.connect(awshost, awsport, keepalive=60)
mqttc.loop_forever()


def handler(event, _):
    # mpg321 doesn't recognize URLs unless they start with http://
    audio_file_url = event['AudioFileUrl'].replace('https://', 'http://')
    subprocess.call(['mpg321', audio_file_url])
