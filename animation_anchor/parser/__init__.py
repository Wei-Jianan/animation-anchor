import sys
from pathlib import Path

mapping_table_root = Path(__file__).parent.joinpath('../assets/mapping_table').resolve()
from collections import namedtuple

VisemeDuration = namedtuple('Viseme', ['viseme', 'begin', 'end'])

from .phonemedurationparser import PhonemeDurationParser
from .cib import Cib
from .animationparser import AnimationParser

def parser_factory(parser_name):
    parser = getattr(sys.modules[__name__], parser_name)
    return parser
