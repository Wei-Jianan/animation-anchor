import os, json
import pypinyin
import tempfile
import subprocess
from collections import namedtuple
from aeneas.executetask import ExecuteTask
from aeneas.task import Task
from aeneas.textfile import TextFile, TextFragment
from aeneas.audiofile import AudioFile
from aeneas.language import Language

PhonemeDuration = namedtuple('Phoneme', ['yinjie', 'begin', 'end'])


class PhonemeForcedAligner:
    def __init__(self):
        self.config_string = u"task_language=zh|is_text_type=plain|os_task_file_format=json"

    def preprocess_text(self, text_path):
        text_file = TextFile(text_path)
        # string_list = list(text.strip())
        # for i, char in enumerate(string_list):
        #     text_file.add_fragment(TextFragment())
        return text_file

    def preprocess_audio(self, audio_path):
        audio_file = AudioFile(audio_path)

        return audio_file

    def execute_align(self, text_path, audio_path):
        abs_text_path = os.path.abspath(os.path.expanduser(text_path))
        abs_audio_path = os.path.abspath(os.path.expanduser(audio_path))
        task = Task(config_string=self.config_string)
        task.audio_file_path_absolute = abs_audio_path
        task.text_file_path_absolute = abs_text_path
        ExecuteTask(task).execute()
        return task

    def postprocess(self, task):
        fragments = task.sync_map_leaves()[1:-1]
        # assert len(fragments) == len(texts), 'the length of aligned phenemes must be equal to the length of texts.'
        # phenemes = pypinyin.pinhyin(texts, style=pypinyin.Style.NORMAL)
        pheneme_durations = [
            {'phoneme': ''.join([pinyin[0] for pinyin in pypinyin.pinyin(fragment.text, style=pypinyin.Style.NORMAL)]),
             'time': str(float(fragment.length))} for fragment in fragments]
        phoneme_durations = [PhonemeDuration(yinjie=pypinyin.pinyin(fragment.text, style=pypinyin.Style.NORMAL)[0][0],
                                             begin=float(fragment.begin),
                                             end=float(fragment.end)) for fragment in fragments]
        return phoneme_durations

    def _write_txt(self, text):
        f = tempfile.NamedTemporaryFile(mode='w', suffix='.txt')
        for char in text:
            if char >= u'\u4e00' and char <= u'\u9fa5':
                f.write(char + '\n')
        f.seek(0)
        return f

    def _write_audio(self, media_path):
        f = tempfile.NamedTemporaryFile(mode='wb', suffix='.wav')
        subprocess.check_call(['ffmpeg', '-y', '-i', media_path, f.name])
        return f

    def align(self, text, media_path):
        # text_file = self.preprocess_text(text)
        # audio_file = self.preprocess_audio(audio_path)
        text_file = self._write_txt(text)
        audio_file = self._write_audio(media_path)
        task_done = self.execute_align(text_file.name, audio_file.name)
        phoneme_durations = self.postprocess(task_done)

        text_file.close()
        audio_file.close()

        return phoneme_durations


if __name__ == '__main__':
    aligner = PhonemeForcedAligner()
    phoneme_durations = aligner.align('春走在路上，看看世界无限宽广，繁花似锦，人来人往，那无人能解的忧伤。', '11.mp3')
    print(phoneme_durations)