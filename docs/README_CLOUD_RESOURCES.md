# Cloud resources setup

## Device-specific resources

For each device of the Talko-Lingo system (typically two), you have to deploy
specific Cloud resources, consisting mostly of what is needed for your device to
authenticate with AWS's `IoT-Data` topics. It will generate certificates which
you can copy to you Raspberry Pi and enable the TalkoLingo service.

To deploy `IoT-Data` credentials to your Raspberry Pi, you can just `make` them:

```
make raspberry-pi-credentials

...make normal outputs...

--------------------------------------------------------
Execute the following on device A terminal:
wget "https://<credentials_bucket>.s3.amazonaws.com/config.zip? \
      AWSAccessKeyId=<ACCESS_KEY_ID>& \
      Signature=<SIGNATURE>& \
      Expires=<TIMESTAMP>" \
      -O config.zip && \
      unzip config.zip -d /home/pi/talko-lingo/.config && \
      rm config.zip
-----------(Link will expire in 15 minutes)-------------
Press enter to continue
```

You can copy-paste this output to your Raspberry Pi, providing that you
