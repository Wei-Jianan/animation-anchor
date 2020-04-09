import json
import csv
from pathlib import Path
from typing import Iterable
from . import mapping_table_root
from . import VisemeDuration
from ..htkaligner import PhonemeDuration

class AnimationParser:
    def __init__(self):
        phoneme_viseme_map_path = Path(mapping_table_root).joinpath('lipshapedict.json')
        with open(phoneme_viseme_map_path, 'r') as load_f:
            self.phoneme_viseme_map = json.load(load_f)['phoneme'] # 音素到视素映射表
        viseme_animation_viseme_map_path = Path(mapping_table_root).joinpath('viseme2animationviseme.csv')
        with open(viseme_animation_viseme_map_path, 'r') as f:
            self.viseme_animation_viseme_map = dict({(line.split()[0], line.split()[1]) if len(line.split()) == 2 else (None, None)
                                                     for line in f.readlines()})

    def phoneme_durations2viseme_durations(self, phoneme_durations: Iterable[PhonemeDuration]) -> Iterable[VisemeDuration]:
        def phoneme2animation_viseme(yinjie):
            return self.viseme_animation_viseme_map[self.phoneme_viseme_map[yinjie]['lipshape']]
        return (VisemeDuration(viseme=phoneme2animation_viseme(phoneme_duration.yinjie),
                               begin=phoneme_duration.begin,
                               end=phoneme_duration.end)
                for phoneme_duration in phoneme_durations)



if __name__ == '__main__':
    AnimationParser()