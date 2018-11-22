import numpy
import timeit

import pyaudio
import soundfile

FORMAT = pyaudio.paInt16  # 16-bit resolution
CHANNEL = 1  # 1 channel
SAMPLE_RATE = 16000  # 44.1kHz sampling rate
CHUNK_SIZE = 16384  # 2^14 samples for buffer


class Recording:
    def __init__(self, filename, audio, device_index):
        print('Creating new recording: ' + filename)
        self.filename = filename
        self.audio = audio
        self.device_index = device_index
        self._audio_file = soundfile.SoundFile(self.filename, mode='w', samplerate=SAMPLE_RATE, channels=CHANNEL)
        self._frames = []
        self._start_time = timeit.default_timer()
        self._stream = self.create_stream()

    def create_stream(self):
        return self.audio.open(
            format=FORMAT,
            rate=SAMPLE_RATE,
            channels=CHANNEL,
            input_device_index=self.device_index,
            input=True,
            frames_per_buffer=CHUNK_SIZE,
        )

    def write_frames(self):
        try:
            audio_data = self._stream.read(CHUNK_SIZE)
        except IOError as ex:
            if ex[1] != 'Input overflowed':
                raise
            audio_data = '\x10' * CHUNK_SIZE
            self._restart_stream()
        self._audio_file.write(numpy.hstack([numpy.fromstring(audio_data, dtype=numpy.int16)]))

    def complete(self):
        self._stream.stop_stream()
        self._stream.close()
        self._audio_file.close()

        duration = timeit.default_timer() - self._start_time
        print('Audio clip created with a duration of ' + str(duration) + ' secs')

    def _restart_stream(self):
        print('Input Overflowed, restarting stream...')
        self._stream.close()
        self._stream = self.create_stream()
