"""In-process ddddocr adapter. Executed only inside _worker.py."""
from captcha_preprocess import image_size
from ddddocr_engine import CaptchaEngine

class Api:
    def __init__(self, globalArgd):
        self.global_args = globalArgd or {}
        self.engine = CaptchaEngine(self.global_args)
        self.args = {}

    def start(self,args):
        self.args = args or {}
        mode = self.args.get('mode','beta')
        names = {'classic':['classic'],'beta':['beta'],'dual':['beta','classic'],
                 'race':['beta','classic'],'custom':['custom']}.get(mode)
        if names is None:
            return '[Error] Unknown ddddocr mode'
        try:
            for name in names:
                self.engine.get_engine(name,self.args)
            return ''
        except Exception as exc:
            return '[Error] '+str(exc)

    def runBytes(self,data):
        try:
            width,height = image_size(data)
            result = self.engine.run(data,self.args)
            if not self.global_args.get("keep_loaded", True):
                self.engine.close()
            text = str(result.get('text',''))
            score = float(result.get('score',0))
            length = int(self.args.get('expected_length',4))
            if not text or (self.args.get('strict_length',True) and len(text)!=length) or score<float(self.args.get('min_confidence',0)):
                return {'code':101,'data':''}
            return {'code':100,'data':[{'text':text,'score':round(max(0,min(1,score)),4),
                                       'box':[[0,0],[width-1,0],[width-1,height-1],[0,height-1]]}]}
        except Exception as exc:
            return {'code':104,'data':'[Error] '+str(exc)}

    def stop(self):
        self.engine.close()
