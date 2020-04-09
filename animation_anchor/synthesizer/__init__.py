from pathlib import Path
template_root = Path(__file__).parent.joinpath('../assets/template').resolve()


from .templateseq import TemplateFrameSeq
from .videosynthesizer import VideoSynthesizer
