# -*- coding: utf-8 -*-
import os
import json


class PhonemeDurationParser:
    def __init__(self, mapping_table_name):
        mapping_table_root = os.path.join(os.path.dirname(__file__), '../assets/mapping_table')
        path_to_phoneme_map_viseme = os.path.join(mapping_table_root, mapping_table_name)
        with open(path_to_phoneme_map_viseme, 'r') as load_f:
            self.phoneme_map_viseme = json.load(load_f)  # 音素到视素映射表

        # self.path_to_phoneme_seq=path_to_phoneme_seq
        # with open(path_to_phoneme_seq,'r') as load_d:
        # self.phoneme_seq_data=json.load(load_d)#音素数据
        # self.visemes=[]
        long_dict = ['zh', 'ch', 'sh']
        long_dict2 = ['ng']

    # def phoneme_json_to_list(self):
    # self.character_phoneme_seq=v['text']
    def phoneme_split(self, A_text):
        text = A_text['phoneme']
        phoneme = []
        if len(text) == 1:
            phoneme.append(text)
        else:
            if text[0:2] in self.long_dict:
                phoneme.append(text[0:2])
                text = text[2:]
            if text[-2:] in self.long_dict2:
                len_text = len(text) - 2
                for j in range(0, len_text):
                    phoneme.append(text[j])
                phoneme.append(self.long_dict2[0])
            else:
                len_text = len(text)
                for j in range(0, len_text):
                    phoneme.append(text[j])
        return phoneme

    def single_parse(self, A_text):
        visemes=[]
        weight = 0
        synaller = self.phoneme_split(A_text)
        len_synaller = len(synaller)
        for j in range(0, len_synaller):
            syllable = synaller[j]
            weight += float(self.phoneme_map_viseme['phoneme'][syllable]['weight'])
        for k in range(0, len_synaller):
            syllable = synaller[k]
            time = float(A_text['time']) * (float(self.phoneme_map_viseme['phoneme'][syllable]['weight']) / weight)
            #time = round(time, 2)
            viseme = self.phoneme_map_viseme['phoneme'][syllable]['lipshape']
            visemes.append((viseme,time))
            
        return visemes

    def parse(self, phoneme_duration_str):
        # with open(path_to_phoneme_seq, 'r') as load_d:
        phoneme_seq_data = json.loads(phoneme_duration_str)  # 音素数据
        # for A_text in phoneme_seq:
        viseme_seq = []
        for A_text in phoneme_seq_data['text']:
            viseme_seq.extend(self.single_parse(A_text))
        return viseme_seq
