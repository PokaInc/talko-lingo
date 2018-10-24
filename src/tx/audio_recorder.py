import os
import tempfile

import pyaudio

from recording import Recording


class AudioRecorder:
    def __init__(self, recording_device_name):
        self.audio = pyaudio.PyAudio()
        self.device_index = self._get_recording_device_index(recording_device_name)
        self._current_recording = None
        self._recordings = []
        self._audio_files_temp_dir = tempfile.mkdtemp()
        self.completion_callback = lambda *args: None

    def __enter__(self):
        return self

    def _get_recording_device_index(self, recording_device_name):
        for i in range(self.audio.get_device_count()):
            if recording_device_name in self.audio.get_device_info_by_index(i).get('name'):
                return i
        raise RuntimeError('Unable to find device named: ' + recording_device_name)

    def _create_recording_file_name(self):
        return os.path.join(self._audio_files_temp_dir, 'input-{}.flac'.format(len(self._recordings)))

    def tick(self, button_pressed):
        if button_pressed:
            if not self._current_recording:
                self._current_recording = Recording(self._create_recording_file_name(), self.audio, self.device_index)
                self._recordings.append(self._current_recording)

            self._current_recording.write_frames()
        else:
            if self._current_recording:
                self._current_recording.complete()
                self.completion_callback(self._current_recording)
                self._current_recording = None

    def __exit__(self, _, __, ___):
        self.audio.terminate()
