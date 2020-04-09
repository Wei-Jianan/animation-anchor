import os
import json
class Cib:

    #long_dict = ['zh', 'ch', 'sh']
    #long_dict2 = ['ng']
    def __init__(self, mapping_table_name):
        mapping_table_root = os.path.join(os.path.dirname(__file__), '../assets/mapping_table')
        path_to_phoneme_map_viseme = os.path.join(mapping_table_root, mapping_table_name)
        with open(path_to_phoneme_map_viseme, 'r') as load_f:
            self.phoneme_map_viseme = json.load(load_f)  # 音素到视素映射表


    def parse(self, phoneme_duration_str):
        # with open(path_to_phoneme_seq, 'r') as load_d:
        print(phoneme_duration_str)
        phoneme_seq_data = json.loads(phoneme_duration_str)  # 音素数据
        # for A_text in phoneme_seq:
        viseme_seq = []
        for i in range(0, len(phoneme_seq_data['text'])):
            viseme = self.phoneme_map_viseme['phoneme'][phoneme_seq_data['text'][i]['phoneme']]['lipshape']
            time =float( phoneme_seq_data['text'][i]['time'])
            viseme_seq.append((viseme, time))
        #viseme_seq = []

        #for A_text in phoneme_seq_data['text']:
           # viseme_seq.extend(self.single_parse(A_text))
            #ww.append(self.weight)
        return viseme_seq
