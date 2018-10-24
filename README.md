# Talko-Lingo
A demonstration project for the re:Invent Builder's Fair

## Abstract

### Talko-Lingo: The multilingual Walkie Talkie

Talko-Lingo enables near real-time communication between two people of the same
or different languages. Users interface with a Walkie Talkie consisting of a
Raspberry Pi embedded into a 3D printed device. After selecting their language,
each user can seamlessly communicate with the recipient, who may be speaking a
different language. The project leverages AWS cloud technologies to encode each
user's voice, transcribe it, translate it to the target language and then
finally convert the translated text to speech. Built-in display mechanisms
provide visual feedback of the translation process.


### Local macOS development

#### Installation
```
xcode-select --install
brew install portaudio
pip install -r requirements.txt
pip install -r requirements_dev.txt

export RECORDING_DEVICE_NAME='Built-in Microphone'
export AUDIO_FILE_STORE=talkolingo-transcribe-talkolingowebsitebucket-12ma3icabs3n6
```
