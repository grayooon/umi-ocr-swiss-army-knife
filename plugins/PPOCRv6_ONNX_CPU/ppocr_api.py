from pathlib import Path
try:
    from ._bridge import Bridge
except ImportError:
    from _bridge import Bridge

class Api(Bridge):
    def __init__(self, globalArgd):
        super().__init__(Path(__file__).resolve().parent, 'ppocr_backend', globalArgd)
