# Raspberry Pi Setup

### Overview
We'll start by configuring the Pi and installing the required softwares. We'll
then clone the project add the appropriate environment variables. Once we get
the code running and we're satisfied wit the setup, we'll duplicate the Micro SD
card so we can get the second Raspberry Pi working without manual interactions.

## Configuring the Pi

### Installing the OS
First you need to get [Raspbian Stretch Lite](https://www.raspberrypi.org/downloads/raspbian/) installed on a Micro SD
Card. I won't go into too much details as there is already great
[documentation](https://www.raspberrypi.org/documentation/installation/installing-images/README.md) that can be found
on the official Raspberry Pi website.

### Getting access to the terminal

There's a few ways to get access to your Raspberry Pi's terminal, but one of the simplest one is just to plug a keyboard
 and a monitor. You'll then need to login, by default the username is `pi` and the password is `raspberry`.

### Basic configuration
In the terminal run the Raspberry Pi configurator:
```
sudo raspi-config
```

#### Change the default password
Considering your Pi will have to be connected to the internet, start by changing the default password to something
else.

#### Network configuration
Open the `Network Options` menu. Change the hostname to something like `talko-a`. Unless you planned to use an ethernet
cable to connect to the internet you'll have to setup the `Wi-fi`. Start by setting the name of your Wi-fi (SSID) and
then input the password. A good way to make sure the Wi-fi was properly configured is to run the `Update` command from
`raspi-config`.

#### Interfacing configuration
Still in `raspi-config`, now navigate to `Interfacing Options`. If you're planning to connect to your Raspberry Pi's
terminal with your computer instead of relying on the keyboard and monitor combo, enable SSH. Then enable I2C as it is
required for the LED display and possibly the speaker bonnet.


### Software installation

In the terminal run the following commands:
```
sudo apt-get update
sudo apt-get install -y build-essential python-dev python-pip python-smbus python-imaging git libportaudio2 portaudio19-dev libsndfile1 libffi-dev mpg321
```

There is a special dependency that needs to be installed for the LED
alphanumerical display to work.
```
git clone https://github.com/adafruit/Adafruit_Python_LED_Backpack.git
cd Adafruit_Python_LED_Backpack
sudo python setup.py install
```

Finally, install [Adafruit's Speaker Bonnet](). You can find the detailed instructions on their [website tutorial](https://learn.adafruit.com/adafruit-speaker-bonnet-for-raspberry-pi/raspberry-pi-usage), but in our case, here is the simplest method what worked for us:

```
curl -sS https://raw.githubusercontent.com/adafruit/Raspberry-Pi-Installer-Scripts/master/i2samp.sh | bash
```

It will ask you to confirm install-steps two times by pressing `y`, then you
will have to reboot the Pi for the changes to take effect.

#### Optional peaker bonnet tweaks

Then, for a clearer sound and to enable volume control, you should follow [these Adafruit instructions](https://learn.adafruit.com/adafruit-speaker-bonnet-for-raspberry-pi/i2s-tweaks) on the Pi:

First, add this line to `/boot/config.txt`:
```
dtoverlay=i2s-mmap
```

### Device-specific AWS resources

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

You can copy-paste this output to your Raspberry Pi; What is happening here is
that when generating the AWS `IoT-Data` credentials, the `make` script uploads
the credentials (certificates) to an S3 bucket and generates a signed link that
only lasts for 15 minutes for security measures. Then, it unzips the files to
the correct configuration directory to be able to publish to the good `IoT-Data`
topic.

### Talko-Lingo installation
In the pi's home directory (`/home/pi`) clone the project:
```
git clone https://github.com/PokaInc/talko-lingo.git
```
cd in the project folder for the next part:
```
cd talko-lingo
```

Install python requirements (be patient it takes a few minutes):
```
cd talko-lingo
pip install -r local_requirements.txt
```

Finally install the `systemd` service on the Raspberry Pi:
```
make install-raspberry-pi-service
```

Which
